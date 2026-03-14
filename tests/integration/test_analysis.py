from __future__ import annotations


class TestGetTemplate:
    async def test_valid_template_types(self, client):
        for template_type in ("interview", "sales", "client", "other"):
            res = await client.get(f"/api/templates/{template_type}")
            assert res.status_code == 200, f"Failed for type: {template_type}"
            assert "template" in res.json()
            assert len(res.json()["template"]) > 0

    async def test_invalid_template_type(self, client):
        res = await client.get("/api/templates/nonexistent")
        assert res.status_code == 404
