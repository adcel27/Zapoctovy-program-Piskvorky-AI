# Zapoctovy-program-Piskvorky-AI
Zápočtový program implementující hru Piškvorky (Gomoku) na standardní hrací desce 15x15 s umělou inteligencí.

## Návod na instalaci a spuštění

Tento program je napsán v jazyce Python a používá pouze standardní knihovny `math` a `random`.

### Požadavky

Nainstalovaný Python 3

### Spuštění programu

1. Stáhněte soubor `Zápočtový program Celecký.py` do svého počítače.
2. Otevřete terminál (příkazovou řádku) ve složce se staženým souborem.
3. Spusťte program příkazem:
   ```bash
   python Zápočtový program Celecký.py
   
## Popis programu
Počítač si pamatuje matice, které určují sílu jednotlivých tahů pro hráče X a O. Po každém zahraném tahu upraví hodnoty 32 nejbližších potenciálních tahů a      následně vybírá své další tahy pouze z několika nejsilnějších možností. Na těchto tazích pak spouští minimax algoritmus do uživatelem stanovené hloubky.

Při výběru tahu program navíc zvažuje, zda některý z hráčů nemůže vyhrát pomocí VCF (Victory by Continuous Four). 

Hra také aktivně uznává jako výhru pouze řadu právě pěti symbolů a ignoruje delší řady. Hráč má rovněž možnost vrátit svůj poslední tah.

Je možné hrát proti třem úrovním přemýšlení počítače: 
#### lehká (hloubka přemýšlení 4, počítač hraje tahy rychle), 
#### střední (hloubka 6), 
#### těžká (hloubka 8, počítač bude v delších partiích trávit znatelně víc čadu přemýšlením, ale bude hrát promyšlenější tahy.

Kromě samotné hry proti počítači může hráč zvolit mód analýzy pozice, kdy počítač hraje tahy sám proti sobě.
Hráč poté musí zvolit hloubku přemýšlení a kolik tahů má počítač celkem provést. 
