# AI Impact Report Demo (Streamlit)

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## What it does
- Single-screen demo that generates an "AI Impact Report" for VAT change (restaurants/catering).
- Uses a transparent scenario model (formulas) + editable Real Data Pack in `data.json`.
- Exports a DOCX report.

## Customize
- Edit `data.json`:
  - `turnover_sector_I_bgn` and `employment_sector_I` with latest NSI numbers
  - scenario presets (Optimistic/Base/Pessimistic)
