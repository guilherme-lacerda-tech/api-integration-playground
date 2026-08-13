from __future__ import annotations


class TransientApiError(RuntimeError):
    pass


class MockPagedApi:
    def __init__(self) -> None:
        self.calls = 0
        self.records = [{"id": f"REC-{i:03d}", "status": "ok"} for i in range(1, 8)]

    def authenticate(self, client_id: str, client_secret: str) -> str:
        if client_id == "demo-client" and client_secret == "demo-secret":
            return "synthetic-token"
        raise PermissionError("invalid synthetic credentials")

    def list_records(self, token: str, page: int, page_size: int) -> dict:
        if token != "synthetic-token":
            raise PermissionError("invalid token")
        self.calls += 1
        if self.calls == 1:
            raise TransientApiError("synthetic transient failure")
        start = (page - 1) * page_size
        end = start + page_size
        return {"items": self.records[start:end], "next_page": page + 1 if end < len(self.records) else None}
