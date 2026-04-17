$printer = Get-CimInstance -Class Win32_Printer -Filter "Name='iR-ADV 6855'"
Invoke-CimMethod -InputObject $printer -MethodName SetDefaultPrinter

$Directory = "C:\<set-path>\qp"

Get-ChildItem -path $Directory -recurse -include *.pdf | Sort-Object Name | 
ForEach-Object {
    Start-Process -FilePath $_.fullname -Verb Print
    Start-sleep 10
    get-process Acrobat | stop-process -Force
    remove-item $_.FullName -verbose -Force
}
