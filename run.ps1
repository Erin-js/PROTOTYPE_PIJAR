$ErrorActionPreference = 'Stop'
$pijarRoot = $PSScriptRoot
Push-Location -LiteralPath $pijarRoot
try {
    $env:PIJAR_STORAGE_MODE = 'local'
    $pijarPython = Join-Path $pijarRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $pijarPython)) {
        python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Pembuatan lingkungan Python gagal. Pastikan Python 3.12 tersedia.' }
    }
    & $pijarPython -c "import streamlit, plotly, pandas, numpy, sklearn, scipy"
    if ($LASTEXITCODE -ne 0) {
        & $pijarPython -m pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) { throw 'Pemasangan dependensi gagal. Periksa koneksi internet.' }
    }
    & $pijarPython -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true
}
finally { Pop-Location }
