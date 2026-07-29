import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

REPO_PATH = "/home/user/fusiondataconversion"

CODE_EXTENSIONS = {".sql", ".pkb", ".pkh", ".txt", ".xml", ".csv", ".ctl"}

MODULE_KEYWORDS = {
    "01": ["introduction", "atp", "autonomous", "database", "sql developer", "connect", "user", "create", "grant", "privileges", "wallet"],
    "02": ["data conversion", "process", "steps", "lifecycle", "wave", "cutover"],
    "03": ["fbdi", "file based data import", "fbl", "file based loader", "adfdi", "spreadsheet", "soap", "rest api", "methodology", "methodologies", "bulk"],
    "04": ["use case", "gl journal", "general ledger", "journal mapping", "report details"],
    "05": ["load data", "staging table", "gl_interface_stg", "csv", "sequence", "trigger"],
    "06": ["extract", "report service", "reportservice", "acl", "access control list", "bi report", "xdm", "xdo", "invoke report"],
    "07": ["packages", "data extraction", "xx_common_util", "xx_webservice_util", "xx_sync_data_bw_fusion_db", "decode_base64", "convert_to_xml"],
    "08": ["synchronize", "sync", "dbms_scheduler", "scheduler", "job", "program", "schedule", "repeat_interval", "freq"],
    "09": ["cross references", "ledger", "lookup", "gl_das", "das ledger"],
    "10": ["scheduler service", "schedule report", "ftp", "delivery channel", "schedulerservice"],
    "11": ["schedule service vs report service", "comparison", "difference"],
    "12": ["data quality", "pre-validate", "validation", "error", "assessment", "prevld", "pre_vld"],
    "13": ["importbulkdata", "import bulk data", "erp integration service", "soap payload", "base64", "ucm", "ess job", "load interface file"],
    "14": ["automate", "e2e", "end to end", "automation", "import journal", "dbms_sql", "blob"],
    "15": ["packages", "migration automation", "xx_imp_bulk_data_in_fusion", "xx_webservice_util_v2", "xx_common_util_v2", "parameters_lookup"],
    "16": ["automation framework", "build framework", "template", "ctl", "xlsm", "entity", "metadata", "object"],
    "17": ["export data", "atp database", "export from db"],
    "18": ["import management", "file based loader", "fbl", "importactivities", "country structure", "import queue"],
    "19": ["rest api", "get", "post", "update", "delete", "patch", "ar invoice", "receipts", "invoke rest", "apex_web_service", "make_request"],
    "20": ["soap service", "wsdl", "purchase order", "create po", "get po", "invoke soap", "apex_web_service"],
    "21": ["adfdi", "spreadsheet loader", "daily rates", "gl_daily_rates", "adl"],
}

MODULE_TITLES = {
    "01": "Introduction - ATP Database, SQL Developer & User Management",
    "02": "Data Conversion Process",
    "03": "Data Conversion Methodologies in Fusion (FBDI, FBL, ADFdi, SOAP, REST)",
    "04": "Use Case - GL Journal Data Migration",
    "05": "Load Data to ATP Database (Staging Tables)",
    "06": "Extract Data from Fusion using ReportService",
    "07": "Develop Packages for Data Extraction",
    "08": "Synchronize Data From Fusion to Database (DBMS_SCHEDULER)",
    "09": "Populate All Cross References",
    "10": "Extract Data from Fusion using SchedulerService",
    "11": "Schedule Service vs Report Service",
    "12": "Assess Data Quality / Pre-Validate Data",
    "13": "Import Bulk Data into Fusion from Database (importBulkData SOAP)",
    "14": "Automate the Import Bulk Data Process (E2E)",
    "15": "Develop Packages for Data Migration Automation",
    "16": "Build Automation Framework for Data Migration",
    "17": "Export Data from ATP Database",
    "18": "Import Management - File Based Loader (FBL)",
    "19": "Invoke REST APIs (GET, POST, UPDATE, DELETE) from Database",
    "20": "Invoke SOAP Service from Database",
    "21": "Import Data through ADFdi Spreadsheet Loader",
}


def extract_pdf_text(pdf_path: str) -> str:
    try:
        import PyPDF2
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
        return text.strip()
    except Exception:
        return ""


def read_code_file(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def build_knowledge_base() -> Dict:
    kb = {}
    repo = Path(REPO_PATH)

    for module_dir in sorted(repo.iterdir()):
        if not module_dir.is_dir() or module_dir.name.startswith(".") or module_dir.name == "fusion-agent":
            continue

        # Extract module number (e.g. "01" from "01. Introduction")
        match = re.match(r"^(\d+)\.", module_dir.name)
        if not match:
            continue

        module_num = match.group(1).zfill(2)
        module_title = MODULE_TITLES.get(module_num, module_dir.name)

        content_parts = []
        files_found = []

        for file_path in sorted(module_dir.rglob("*")):
            if not file_path.is_file():
                continue

            ext = file_path.suffix.lower()
            rel_path = str(file_path.relative_to(repo))

            if ext == ".pdf":
                text = extract_pdf_text(str(file_path))
                if text:
                    content_parts.append(f"--- PDF: {file_path.name} ---\n{text}")
                    files_found.append(rel_path)

            elif ext in CODE_EXTENSIONS and file_path.stat().st_size < 100_000:
                text = read_code_file(str(file_path))
                if text:
                    content_parts.append(f"--- FILE: {file_path.name} ---\n{text}")
                    files_found.append(rel_path)

        if content_parts:
            kb[module_num] = {
                "title": module_title,
                "keywords": MODULE_KEYWORDS.get(module_num, []),
                "content": "\n\n".join(content_parts),
                "files": files_found,
            }

    return kb


def _score_module(module: Dict, query: str) -> int:
    query_lower = query.lower()
    query_words = set(re.findall(r"\w+", query_lower))
    score = 0

    # Keyword match (weighted higher)
    for kw in module["keywords"]:
        if kw in query_lower:
            score += 3
        elif any(w in kw for w in query_words if len(w) > 3):
            score += 1

    # Title match
    title_words = set(re.findall(r"\w+", module["title"].lower()))
    score += len(query_words & title_words) * 2

    # Content match (light scan)
    content_snippet = module["content"][:3000].lower()
    for word in query_words:
        if len(word) > 3 and word in content_snippet:
            score += 1

    return score


def search_modules(kb: Dict, query: str, top_k: int = 3) -> List[str]:
    scored = [(num, _score_module(mod, query)) for num, mod in kb.items()]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [num for num, score in scored[:top_k] if score > 0]


def format_context(kb: Dict, module_nums: List[str], max_chars: int = 15000) -> str:
    parts = []
    total = 0
    for num in module_nums:
        if num not in kb:
            continue
        mod = kb[num]
        header = f"\n{'='*60}\nMODULE {num}: {mod['title']}\n{'='*60}\n"
        content = mod["content"]
        remaining = max_chars - total - len(header)
        if remaining <= 0:
            break
        chunk = header + content[:remaining]
        parts.append(chunk)
        total += len(chunk)
    return "\n".join(parts)


def get_all_module_titles(kb: Dict) -> List[Tuple[str, str]]:
    return [(num, mod["title"]) for num, mod in sorted(kb.items())]
