from openpyxl import load_workbook

from amb_core.export import export_all, render_html


def test_all_formats_written(sample_run, tmp_path):
    memo, ctx = sample_run
    paths = export_all(memo, ctx, tmp_path)
    for k in ["md", "json", "html", "xlsx"]:
        assert paths[k].exists() and paths[k].stat().st_size > 0


def test_html_contains_shortlist_and_audit(sample_run):
    memo, _ = sample_run
    h = render_html(memo)
    assert memo.shortlist[0].name in h
    assert "claims verified" in h


def test_xlsx_has_expected_sheets(sample_run, tmp_path):
    memo, ctx = sample_run
    paths = export_all(memo, ctx, tmp_path)
    wb = load_workbook(paths["xlsx"])
    assert {"Shortlist", "Metrics", "Audit"}.issubset(set(wb.sheetnames))
