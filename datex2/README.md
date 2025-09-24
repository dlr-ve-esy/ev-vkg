# DATEX II to Relational CSV

These scripts extract transform datex 2 datasets of multiple countries to
relational csv databases following a relational model designed to be
interoperable with the virtual knowledge graph. These are scripts designed to
work with specific releases of the DATEX II feeds. Unfortunately these can
easily change, please open an issue if any of these feeds does not longer work:

- [Germany](https://mobilithek.info/offers/855030183015186432)
- [Spain](https://nap.dgt.es/dataset/puntos-de-recarga-electrica-para-vehiculos)
- [Portugal](https://nap-portugal.imt-ip.pt/nap/multimodalsupplydetail/148)
- [Latvia](https://transportdata.gov.lv/en/card/978835ee-f55b-481c-9791-ba0395d3619a)
- [Slovenia](https://www.nap.si/en/datasets_details?id=acc8a643-9dac-ecad-58da-0ce20f88f4bd)
- [Austria](https://admin.ladestellen.at)

These feeds are known to be incompatible:

- [Hungary](https://napportal.kozut.hu/en/#/configuration/data-provider/profile/28)
- [Cyprus](http://www.traffic4cyprus.org.cy/api/3/action/package_show?id=electricvehiclecharges)

The scripts expect a metadata.csv file with a bunch of sources, it can be
adapted to use glob at line 11. Run  `parse.xml` or `parse.json` (only works for
Austria) depending on the data you got. Once done you get a tabular database for
each dataset. Run `restructure_annotate.py` for some QoL adjustments.