#!/bin/bash

# see https://fias.nalog.ru/Updates
curl https://fias.nalog.ru/docs/%D0%92%D1%8B%D0%B3%D1%80%D1%83%D0%B7%D0%BA%D0%B0%20%D0%B8%D0%B7%20%D0%A4%D0%98%D0%90%D0%A1%20%D0%B2%20XML%20xsd%20%D1%81%D1%85%D0%B5%D0%BC%D1%8B%20%D1%81%2009%20%D0%B8%D1%8E%D0%BD%D1%8F%202016%20%D0%B3%D0%BE%D0%B4%D0%B0.zip \
  --output fias.zip
unzip -o fias.zip && rm fias.zip