from datetime import datetime
from zoneinfo import ZoneInfo


def get_current_date(tz_name="UTC"):
    return datetime.now().astimezone(ZoneInfo(tz_name)).strftime("%Y-%m-%dT%H:%M:%S.%f%z")


def simplify_author(cur_obj: dict):
    simplified_obj = cur_obj.copy()
    if 'author' in cur_obj:
        simplified_obj['author'] = cur_obj['author']['name']
    if 'updateAuthor' in cur_obj:
        simplified_obj['updateAuthor'] = cur_obj['updateAuthor']['name']
    return simplified_obj


def simplify_raw_dict(raw_obj: dict):
    simplified_obj = raw_obj.copy()
    # Filter out fields with None as its value
    simplified_obj['fields'] = {k: v for k, v in simplified_obj['fields'].items() if v is not None}
    # Remap field names
    field_names = simplified_obj.pop('names', None)
    if field_names:
        for field_name, rendered_field_name in field_names.items():
            if field_name in simplified_obj['fields']:
                simplified_obj['fields'][rendered_field_name] = simplified_obj['fields'].pop(field_name)
    return simplified_obj


def find_all(jcli, jql_str, simplify_raw=True):
    print(f"Searching for tickets with: {jql_str}")
    results = []
    i = 0
    chunk_size = 50
    while True:
        chunk = jcli.search_issues(jql_str=jql_str, startAt=i, maxResults=chunk_size, expand="names,changelog")
        i += chunk_size
        results += chunk.iterable
        print(f"Batch {i/chunk_size}: Got {len(chunk.iterable)} tickets")
        if i >= chunk.total:
            break
    print(f"Found {len(results)} tickets")
    if simplify_raw:
        for result in results:
            result.raw = simplify_raw_dict(result.raw)
        print(f"Simplified {len(results)} tickets' raw")
    return results
