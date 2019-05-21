# Medcel_Python_Scripts
A collection of Python scripts created throughout the time I worked at Medcel for personal use at work.

All Python scripts from this project run on **Python 3.7**
___

## MedGrupo_Web_Scrapper
Script made specially to get all approved students that studied at MedGrupo; an information widely available in their own website.

This script was specially hard due to a _heavily reliable javascript page_ and because of their _buggy_ website (seriously, fix the mobile version...).

### 1. Requirements
Run the script `pip install -r requirements.txt` (use `sudo` if running on Mac or Linux).

You'll also need [Google Chrome](https://www.google.com/chrome/). Once installed, check the **version** under `More > Help > About Google Chrome`.

Then, download the specific [webdriver](http://chromedriver.chromium.org/downloads) version for your OS. Unzip and place the webdriver on the **same folder as the _main script_**.

### 2. Usage
To use the program with command line attributes, use:
```
	python3 web_scrapper_medgrupo.py [-d | --Debug] [-n | --Notify] [-s | --Skip]
		[-sa | --Skip_All] [-c | --Concatenar] [-sc | --Somente_Concatenar]
	  * [-a | --Ano]
	  * [-e | --Estado]
	  * [-ia | --Instituicao_Aprovados]
	  * [-it | --Instituicao_Todos]
```
(Use just 1 command with * at a time)

Type `python3 web_scrapper_medgrupo.py -h` or `python3 web_scrapper_medgrupo.py --Help` to see a list with all the commands and its purpose.

It's also possible to use without command line attributes. In that case just type:
`python3 web_scrapper_medgrupo.py`

___