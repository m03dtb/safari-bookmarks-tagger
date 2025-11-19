#!/usr/bin/env bash

# executable erstellen
pyinstaller --onefile --windowed --name BookmarksTagger main.py

echo ""
echo "-----------------------------------------------------------------------"
echo "INSTALLATION ERFOLGREICH"
echo "-----------------------------------------------------------------------"
echo ""
echo "BITTE FOLGENDE SCHRITTE AUSFUEHREN:"
echo "danach: dist/BookmarksTagger.app in die /Applications/ kopieren"
echo "unter 'Apple-Icon' -> Systemeinstellungen -> Datenschutz & Sicherheit: Festplattenvollzugriff:"
echo "fuer 'BookmarksTagger.app' Festplattenvollzugriff erlauben"
