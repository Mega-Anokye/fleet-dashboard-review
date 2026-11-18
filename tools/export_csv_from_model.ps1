param([int]$Port, [string]$OutDir)
Add-Type -Path "C:\Program Files\On-premises data gateway\Microsoft.AnalysisServices.AdomdClient.dll"
$conn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection("Data Source=localhost:$Port")
$conn.Open()
$inv = [System.Globalization.CultureInfo]::InvariantCulture
$enc = [System.Text.Encoding]::GetEncoding(1252)

$specs = @(
  @{ File = "fuel_sheet_actros_usd.csv"; Table = "Fuel"; Order = "SN";
     Cols = @("SN","Truck ID","Date","Pump Location","Fill / Lit","Start ODO","End ODO","Coupon #","Route","Route#","Veh Type","Deployment","Driver Name","Dist Covered","Km / Lit","Remarks") },
  @{ File = "maintenance_log_actros_usd.csv"; Table = "Maintenance"; Order = "SN";
     Cols = @("SN","Truck ID","Date","Maintenance Type","Priority","Description","Part Replaced","Mechanic Name","Downtime_Days","Cost_USD","Remarks") },
  @{ File = "driver_performance_actros_usd.csv"; Table = "DriverPerformance"; Order = "Driver Name";
     Cols = @("Driver Name","Truck ID","Trips Completed","Total Hours Driven","Safety Score","Harsh Braking Events","Over-Speeding Events","Excessive Idling Mins","Late Deliveries","Fuel ECO Rating") }
)

foreach ($s in $specs) {
  $sel = ($s.Cols | ForEach-Object { "`"c$([array]::IndexOf($s.Cols, $_))`", '$($s.Table)'[$_]" }) -join ", "
  $q = "EVALUATE SELECTCOLUMNS('$($s.Table)', $sel) ORDER BY [c$([array]::IndexOf($s.Cols, $s.Order))]"
  $cmd = $conn.CreateCommand(); $cmd.CommandText = $q
  $r = $cmd.ExecuteReader()
  $lines = New-Object System.Collections.Generic.List[string]
  $lines.Add(($s.Cols -join ","))
  $commaHits = 0
  while ($r.Read()) {
    $vals = for ($i = 0; $i -lt $r.FieldCount; $i++) {
      $v = $r.GetValue($i)
      if ($v -is [DBNull] -or $null -eq $v) { "" }
      elseif ($v -is [datetime]) { $v.ToString("dd/MM/yyyy", $inv) }
      elseif ($v -is [double] -or $v -is [decimal]) { ([double]$v).ToString("0.############", $inv) }
      else { [string]$v }
    }
    $vals = foreach ($x in $vals) {
      if ($x -match '[,"]') { $commaHits++; '"' + $x.Replace('"', '""') + '"' } else { $x }
    }
    $lines.Add(($vals -join ","))
  }
  $r.Close()
  [System.IO.File]::WriteAllLines((Join-Path $OutDir $s.File), $lines, $enc)
  "{0}: {1} rows, values containing commas: {2}" -f $s.File, ($lines.Count - 1), $commaHits
}
$conn.Close()
