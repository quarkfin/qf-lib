#Requires -RunAsAdministrator

# Refreshes the environment variable so that we don't have to restart the terminal
function Refresh-Environment {
    foreach ($level in "Machine", "User") {
        [Environment]::GetEnvironmentVariables($level).GetEnumerator() | % {
            # For Path variables, append the new values, if they're not already in there
            if ($_.Name -match 'Path$') { 
                $_.Value = ($((Get-Content "Env:$($_.Name)") + ";$($_.Value)") -split ';' | Select -unique) -join ';'
            }
            $_
        } | Set-Content -Path { "Env:$($_.Name)" }
    }
}

$ErrorActionPreference = "Stop"

# Install Python
Write-Host "---> installing Python 3.6.8"
Start-Process ./python-3.6.8-amd64.exe -ArgumentList @('/quiet InstallAllUsers=1 PrependPath=1') -Wait
Write-Host "---> python installed"

Refresh-Environment

# Python Virtual Environment
Write-Host "--> creating Python Virtual Environment"
$pathToVenv = Read-Host -Prompt 'Where would you like to create Python Virtual Environment (full path including a name of the Virtual Env.; it will be impossible to change it later on):'
python -m venv "$pathToVenv"
Push-Location $pathToVenv
Scripts\Activate.ps1
Pop-Location
Write-Host "--> Python Virtual Environment created"

Write-Host "--> upgrading pip and setuptools"
python -m pip install --upgrade pip setuptools
Write-Host "--> pip and setuptools upgraded"

# GTK3+
Write-Host "--> installing GTK3+"
Start-Process gtk3-runtime-3.22.21-2017-09-25-ts-win64.exe -ArgumentList @('/S', '/setpath=yes') -Wait
$exitCode = $LastExitCode
If ($exitCode -ne 0) {
    Write-Host "--> Failed to install GTK3+. Exit code: $($exitCode)"
    exit
}
Else {
    Write-Host "--> GTK3+ installed"
}


# Bloomberg
Write-Host "--> installing Bloomberg"
Write-Host "--> extracting Bloomberg C++ SDK to C:\Requirements"
Expand-Archive blpapi_cpp_3.8.18.1-windows.zip -DestinationPath C:\Requirements
Write-Host "--> Bloomberg C++ SDK extracted to C:\Requirements"

Write-Host "--> setting up environment variables for Bloomberg: BLPAPI_ROOT and PATH"
[Environment]::SetEnvironmentVariable('BLPAPI_ROOT', 'C:\Requirements\blpapi_cpp_3.8.18.1\bin', [EnvironmentVariableTarget]::Machine)
[Environment]::SetEnvironmentVariable('PATH', $env:PATH + ';C:\Requirements\blpapi_cpp_3.8.18.1\bin', [EnvironmentVariableTarget]::Machine)
Write-Host "--> environment variables set up"

Write-Host "--> installing Python wheel for Bloomberg"
pip install blpapi-3.9.1-cp36-cp36m-win_amd64.whl
Write-Host "--> Python wheel for Bloomberg installed"


# Numpy, Scipy, Cvxopt, Statsmodels
Write-Host "--> installing numpy from wheel"
pip install numpy-1.15.4+mkl-cp36-cp36m-win_amd64.whl
Write-Host "--> numpy installed"

Write-Host "--> installing scipy from wheel"
pip install scipy-1.1.0-cp36-cp36m-win_amd64.whl
Write-Host "--> scipy installed"

Write-Host "--> installing cvxopt from wheel"
pip install cvxopt-1.2.2-cp36-cp36m-win_amd64.whl
Write-Host "--> cvxopt installed"

Write-Host "--> installing statsmodels from wheel"
pip install statsmodels-0.9.0-cp36-cp36m-win_amd64.whl
Write-Host "--> statsmodels installed"

# TA-Lib
Write-Host "--> installing TA-Lib"
Write-Host "--> extracting TA-Lib C++ SDK to C:\ta-lib"
Expand-Archive ta-lib-0.4.0-msvc.zip -DestinationPath C:\
Write-Host "--> TA-Lib C++ SDK extracted to C:\ta-lib"

Write-Host "--> installing Python wheel for TA-Lib"
pip install TA_Lib-0.4.17-cp36-cp36m-win_amd64.whl
Write-Host "--> Python wheel for TA-Lib installed"

# installing certifi (necessary to avoid some SSL problems with some positions from requirements.txt)
Write-Host "--> installing certifi"
pip install certifi==2017.4.17
Write-Host "--> certifi installed"

# Haver
$InstallPythonRequirements = Read-Host -Prompt "`nInstall Haver (optional)? [y] or [n]"
if ($InstallPythonRequirements -eq "y") {
	Write-Host "--> installing Haver"
	python -m pip install Haver-1.1.0-cp36-cp36m-win_amd64.whl
	Write-Host "--> Haver installed"
}

# install other wheels
Push-Location ../
Write-Host "--> installing remaining project requirements"
pip install -r requirements.txt
Write-Host "--> all project requirements installed"
Pop-Location

# install Interactive Brokers
Write-Host "--> installing Interactive Brokers: TWS"
Start-Process msiexec.exe -ArgumentList '/I TWS_API_Install_973.06.msi /quiet TARGETDIR=C:\' -Wait
$exitCode = $LastExitCode
If ($exitCode -ne 0) {
    Write-Host "--> Failed to install Interactive Brokers TWR. Exit code: $($exitCode)"
    exit
}
Else {
    Write-Host "--> Interactive Brokers TWS installed"
}
Write-Host "--> installing Interactive Brokers: python package"
Push-Location "C:\TWS API\source\pythonclient"
python setup.py install
Pop-Location
Write-Host "--> Interactive Brokers - python package installed"

Write-Host "---> COMPLETED QF-LIB SETUP <---"