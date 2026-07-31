param(
    [string]$Action = "status",
    [int]$WaitSeconds = 15
)

Add-Type -AssemblyName "UIAutomationClient, Version=4.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35"
Add-Type -AssemblyName "UIAutomationTypes, Version=4.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35"

$window = [System.Windows.Automation.AutomationElement]::RootElement.FindFirst(
    [System.Windows.Automation.TreeScope]::Children,
    [System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::NameProperty, "Proton VPN"
    )
)

if (-not $window) {
    Write-Error "ProtonVPN window not found"
    exit 1
}

function Click-Button {
    param([string]$AutomationId)
    $btn = $window.FindFirst(
        [System.Windows.Automation.TreeScope]::Subtree,
        [System.Windows.Automation.PropertyCondition]::new(
            [System.Windows.Automation.AutomationElement]::AutomationIdProperty, $AutomationId
        )
    )
    if ($btn) {
        try {
            $pattern = $btn.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
            $pattern.Invoke()
            Write-Host "Clicked $AutomationId"
            return $true
        } catch {
            Write-Warning "Failed to click ${AutomationId}: $_"
            return $false
        }
    }
    return $false
}

function Get-ElementName {
    param([string]$AutomationId)
    $element = $window.FindFirst(
        [System.Windows.Automation.TreeScope]::Subtree,
        [System.Windows.Automation.PropertyCondition]::new(
            [System.Windows.Automation.AutomationElement]::AutomationIdProperty, $AutomationId
        )
    )
    if ($element) { return $element.Current.Name }
    return $null
}

switch ($Action) {
    "disconnect" {
        Click-Button "ConnectionCardDisconnectButton"
        exit 0
    }
    "connect" {
        Click-Button "ConnectionCardConnectButton"
        exit 0
    }
    "change_server" {
        Click-Button "ConnectionCardDisconnectButton" | Out-Null
        Start-Sleep -Seconds 3
        if (-not (Click-Button "ConnectionCardChangeServerButton")) {
            Write-Warning "Change server button not available, connecting directly"
        }
        Start-Sleep -Seconds 2
        Click-Button "ConnectionCardConnectButton" | Out-Null
        exit 0
    }
    "reconnect" {
        Click-Button "ConnectionCardDisconnectButton" | Out-Null
        Start-Sleep -Seconds 3
        Click-Button "ConnectionCardConnectButton" | Out-Null
        exit 0
    }
    "status" {
        $connected = $null -ne (Get-ElementName "ConnectionCardDisconnectButton")
        if ($connected) {
            $server = Get-ElementName "ConnectionCardTitle"
            Write-Output "Connected to: $server"
        } else {
            Write-Output "Disconnected"
        }
        exit 0
    }
    default {
        Write-Error "Unknown action: $Action. Valid: disconnect, connect, change_server, reconnect, status"
        exit 1
    }
}