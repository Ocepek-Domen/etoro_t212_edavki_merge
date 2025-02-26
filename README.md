# eToro-T212-eDavki 📊💻

Ta projekt je namenjen združevanju podatkov o transakcijah dveh različnih borznih platform (eToro in T212) v eno samo datoteko v skladu z metodo FIFO (First In, First Out) tako, da bo vsebina pravilno usklajena za poročanje v sistemu eDavki. (Doh-KDVP)

### 📝 Opis
Imamo dve XML datoteki:

1. **etoro.xml**: Vsebuje podatke o transakcijah iz platforme eToro. Vsebuje že pravilno razvrščene transakcije po FIFO metodologiji. (Pridobljeno z uporabo https://github.com/masbug/etoro-edavki) 🙏
2. **t212.xml**: Vsebuje podatke o transakcijah iz platforme T212. Transakcije iz te datoteke bodo dodane v etoro.xml. (Pridobljeno z uporabo https://github.com/Neophytez/t212-edavki) 🙏

Cilj je, da dodamo vse transakcije iz t212.xml v etoro.xml, pri čemer morajo biti vsi vnosi pravilno razvrščeni po datumu nakupa (F1) in datumu prodaje (F6). Vse združene transakcije bodo v končni datoteki **merged.xml**.
Pri združevanju se ponovno poračunava polje F8 (zaloga) in polje ID (sequence number).

### ⚠️ Omejitev odgovornosti
Projekt uporabljate na lastno odgovornost. Za morebitne napake, nepravilnosti ali poškodbe, nastale pri uporabi, ne odgovarjam.
Pred oddajo v eDavki ročno preveri merge.xml za vsaj nekaj transakcij.

### TODO 📝
- [ ] ⚠️ Če so v t212.xml transakcije za delnice, katerih ni v etoro.xml, jih trenutno ne dodaja v merged.xml (Spisek teh je v errors.log) ⚠️

### 📁 Struktura projekta
│   etoro.xml
│   main.py
│   README.md
│   t212.xml
└───output
     │──errors.log
     │──info.log
     └──merged.xml

etoro.xml in t212.xml sta primeri datotek, ki vsebujeta transakcijske podatke iz dveh različnih borznih platform.

#### 1️⃣ Namestitev Python okolja
Prepričajte se, da imate nameščen Python 3.13.2.

#### 2️⃣ Namestitev odvisnosti
Za zagon aplikacije ne potrebujete namestiti nobenih odvisnosti, saj so vse odvisnosti nameščene s Pythonom.

#### 3️⃣ Zagon aplikacije
Ko so vse odvisnosti nameščene, zaženite skript z ukazom:
primer:
python3.13.exe c:/Users/Janez/Desktop/etoro_t212_edavki/main.py c:/Users/Janez/Desktop/etoro_t212_edavki/etoro.xml c:/Users/Janez/Desktop/etoro_t212_edavki/t212.xml

### 📝 Pojasnilo datotek:
- **etoro.xml** in **t212.xml** vsebujeta podatke o nakupih in prodajah na borznih platformah.
- **merged.xml** bo vsebovala združene podatke v pravilnem zaporedju FIFO, kjer bodo nakupi in prodaje pravilno razvrščeni po datumu nakupa (F1) in datumu prodaje (F6).
- **errors.log** vsebuje napake pri združevanju
- **info.log** vsebuje informacije o uspešno združenih transakcijah.

### 📜 Licenca
Ta projekt je odprtokoden in objavljen pod MIT licenco, kar pomeni, da ga lahko uporabljaš, spreminjaš in distribuiraš brez omejitev.