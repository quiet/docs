all : quiet quiet-js org.quietmodem.Quiet QuietModemKit

quiet:
	cd site_configs && mkdocs build -f quiet.yml

quiet-js:
	cd site_configs && mkdocs build -f quiet-js.yml

org.quietmodem.Quiet:
	cd site_configs && mkdocs build -f org.quietmodem.Quiet.yml

QuietModemKit:
	cd site_configs && mkdocs build -f QuietModemKit.yml

.PHONY : all quiet quiet-js org.quietmodem.Quiet QuietModemKit
