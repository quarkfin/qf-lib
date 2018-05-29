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

# Check if a program is installed as 32 or 64 bit
function Is-Installed( $program ) {
    $x86 = ((Get-ChildItem "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall") |
            Where-Object { $_.GetValue( "DisplayName" ) -like "*$program*" } ).Length -gt 0;
    $x64 = ((Get-ChildItem "HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall") |
            Where-Object { $_.GetValue( "DisplayName" ) -like "*$program*" } ).Length -gt 0;
    return $x86 -or $x64;
}

$CurrentPath = (Get-Item -Path ".\" -Verbose).FullName

Clear-Host
Write-Host "------------------------------ Installatron 8 ---------------------------------"
Write-Host "This script will install everything you could ever need for the QF Lib`n`n"

# Sets TLS from TLS1 to TLS2, neccessary for https connections
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

Write-Host "---> Searching for installed programs..."

$RequiredInstalls = "Node.js", "Microsoft Build Tools 14.0", "Python 3.5 blpapi-", "Microsoft Visual C++ 2010  x64 Redistributable", "GTK3-Runtime Win64"
$NeedToInstall = @()

for ($i = 0; $i -lt $RequiredInstalls.Length; $i++) {
    if (!(Is-Installed $RequiredInstalls[$i])) {
        $NeedToInstall += $RequiredInstalls[$i]
    }
}

if ($NeedToInstall.Length -eq 0) {
    Write-Host "You have all the required programs installed."
}
else {
    $List = $NeedToInstall -join "`n- "
    Write-Host "`nThere are some programs you need to install:`n- $List`n"
    $Proceed = Read-Host -Prompt "Would you like to install these programs? [y]es, [n]o, or [a]sk me for each one"
    if ($Proceed -eq "y" -or $Proceed -eq "a") {
        Write-Host ""
        for ($i = 0; $i -lt $NeedToInstall.Length; $i++) {
            $Program = $NeedToInstall[$i]
            if ($Proceed -eq "a") {
                $InstallNext = Read-Host -Prompt "`nWould you like to install ${Program}? [y] or [n]"
                if ($InstallNext -eq "n") {
                    continue
                }
            }

            # Install Node.js
            if ($Program -eq $RequiredInstalls[0]) {
                Write-Host "---> Installing Node.js..."
                Invoke-WebRequest -OutFile C:\nodejs.msi "https://nodejs.org/dist/v8.9.1/node-v8.9.1-x64.msi" -UseBasicParsing
                Start-Process msiexec.exe -ArgumentList '/I C:\nodejs.msi /quiet' -Wait | Out-Null
                Remove-Item C:\nodejs.msi
            }
            
            # Install C++ Build Tools
            elseif ($Program -eq $RequiredInstalls[1]) {
                Write-Host "---> Installing Microsoft Build Tools 14.0... (this one takes some time, so be patient)..."
                npm install --global --production windows-build-tools --loglevel silent | Out-Null
            }
            
            # Install Bloomberg
            elseif ($Program -eq $RequiredInstalls[2]) {
                Write-Host "---> Installing Bloomberg..."
                Invoke-WebRequest -OutFile blpapi-3.9.0b1.win-amd64-py3.5.msi "https://cernbox.cern.ch/index.php/s/XVd9BbjJHl4uPZs/download" -UseBasicParsing
                Invoke-WebRequest -OutFile bbg-api.zip "https://software.tech.bloomberg/BLPAPI-Stable-Generic/blpapi_cpp_3.8.18.1-windows.zip" -UseBasicParsing
                
                Expand-Archive bbg-api.zip -DestinationPath C:\Requirements 
                Start-Process msiexec.exe -ArgumentList "/I blpapi-3.9.0b1.win-amd64-py3.5.msi /quiet /qn /norestart" -Wait
                
                Remove-Item blpapi-3.9.0b1.win-amd64-py3.5.msi
                Remove-Item bbg-api.zip
                [Environment]::SetEnvironmentVariable('BLPAPI_ROOT', 'C:\Requirements\blpapi_cpp_3.8.18.1\bin', [EnvironmentVariableTarget]::Machine)
                [Environment]::SetEnvironmentVariable('PATH', $env:PATH + ';C:\Requirements\blpapi_cpp_3.8.18.1\bin', [EnvironmentVariableTarget]::Machine)
            }
            
            # Install VC Redist
            elseif ($Program -eq $RequiredInstalls[3]) {
                Write-Host "---> Installing VC Redist..."
                Invoke-WebRequest -OutFile vc_redist.x64.exe "https://download.microsoft.com/download/9/3/F/93FCF1E7-E6A4-478B-96E7-D4B285925B00/vc_redist.x64.exe" -UseBasicParsing
                Start-Process vc_redist.x64.exe -ArgumentList '/quiet', '/norestart' -Wait
                Remove-Item vc_redist.x64.exe
            }
            
            # Install GTK3
            elseif ($Program -eq $RequiredInstalls[4]) {
                Write-Host "---> Installing GTK3 Runtime..."
                Invoke-WebRequest -OutFile gtk3.exe "https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/download/2017-11-15/gtk3-runtime-3.22.26-2017-11-15-ts-win64.exe" -UseBasicParsing
                Start-Process gtk3.exe -ArgumentList @('/S', '/setpath=yes') -Wait
                Remove-Item gtk3.exe
            }
            
            Refresh-Environment
        }
    }
}

Write-Host "---> COMPLETED SETUP <---"