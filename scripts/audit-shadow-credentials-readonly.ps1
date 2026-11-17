<#
.SYNOPSIS
  Read-only audit helper for Shadow Credentials indicators in an authorized AD lab.
.DESCRIPTION
  Reads the number of registered key credentials on one AD account and audits
  Event ID 5136 entries from a Domain Controller. Does not modify AD, issue
  Kerberos tickets, retrieve credentials, or change security controls.
.PARAMETER Identity
  An existing account name to inspect, e.g. a permitted lab account.
.PARAMETER DomainController
  Domain Controller hostname where AD DS and Security events can be read.
.PARAMETER Days
  Lookback days for Event ID 5136, default 7.
#>
param(
    [Parameter(Mandatory=$true)][string]$Identity,
    [Parameter(Mandatory=$true)][string]$DomainController,
    [ValidateRange(1,30)][int]$Days = 7
)

$ErrorActionPreference = 'Stop'
Import-Module ActiveDirectory -ErrorAction Stop

# Read only: do not print binary key material to the console or files.
$account = Get-ADUser -Identity $Identity -Server $DomainController `
    -Properties 'msDS-KeyCredentialLink','whenChanged'
$keyCredentials = @($account.'msDS-KeyCredentialLink' | Where-Object { $null -ne $_ })
Write-Output ('Account: {0}' -f $account.SamAccountName)
Write-Output ('Registered key credentials: {0}' -f $keyCredentials.Count)
Write-Output ('AD whenChanged: {0}' -f $account.whenChanged)

$since = (Get-Date).AddDays(-$Days)
Write-Output ('Event 5136 search starting: {0}' -f $since)

# Event 5136 exists only when Directory Service Changes auditing and relevant SACL
# permissions are configured. Running the script does not enable these settings.
try {
    $events = Get-WinEvent -ComputerName $DomainController -FilterHashtable @{
        LogName = 'Security'
        Id = 5136
        StartTime = $since
    } -ErrorAction Stop
} catch {
    Write-Warning ('Could not read 5136 events: {0}' -f $_.Exception.Message)
    exit 0
}

$matches = foreach ($event in $events) {
    [xml]$eventXml = $event.ToXml()
    $fields = @{}
    foreach ($node in $eventXml.Event.EventData.Data) {
        $fields[$node.GetAttribute('Name')] = $node.InnerText
    }
    if ($fields['AttributeLDAPDisplayName'] -eq 'msDS-KeyCredentialLink') {
        [PSCustomObject]@{
            TimeCreated = $event.TimeCreated
            Actor = $fields['SubjectUserName']
            ObjectDN = $fields['ObjectDN']
            Attribute = $fields['AttributeLDAPDisplayName']
            Operation = $fields['OperationType']
        }
    }
}

if (@($matches).Count -gt 0) {
    $matches | Sort-Object TimeCreated -Descending | Format-Table -AutoSize
} else {
    Write-Output 'No matching 5136 events found in this period. This does NOT prove no changes occurred.'
}
