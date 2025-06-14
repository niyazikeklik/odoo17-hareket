CREATE OR REPLACE PACKAGE HTML_TABLE_API2 AS

   TYPE string_list IS TABLE OF long;

--Olusturulan tablonun toplam uzunlugunu verilen parametrelere istinaden kontrol eder.

   FUNCTION LENGTH_CHECK (sutunlar IN long, satirlar IN long,  MAX_LENGTH IN NUMBER DEFAULT 32000) RETURN BOOLEAN;

--Birden fazla sutunu tek bir seferde eklemek �c�n.

   FUNCTION SUTUNLAR_EKLE
   (
      p_sutun_adlari IN string_list,
      text_sutunlar  IN long
   ) RETURN long;

 --Sutun Ekler
   FUNCTION SUTUN_EKLE
   (
      p_sutun       IN long,
      text_sutunlar IN long
   ) RETURN long;


  --Sat�r ekler
   FUNCTION SATIR_EKLE
   (
      p_satir_values IN string_list,
      text_satirlar  IN long
   ) RETURN long;



  --Olusturulan HTML tablosunu Text olarak doner
   FUNCTION BUILD_AND_GET_HTML_TABLE
   (
      p_baslik      IN long,
      p_aciklama    IN long,
      text_sutunlar IN long,
      text_satirlar IN long
   ) RETURN long;


   --Paketin nas�l kullan�lacaginin bir ornegi.
   PROCEDURE TEST;

END HTML_TABLE_API2;
/
CREATE OR REPLACE PACKAGE BODY HTML_TABLE_API2 AS

   FUNCTION INIT_TABLE(p_baslik IN LONG, p_aciklama IN LONG) RETURN LONG IS
      html_table LONG;
   BEGIN

      html_table := '
      <style>#customers {
      border-collapse: collapse;
      }
      #customers td, #customers th
      {
                 border: 1px solid #ddd; padding: 8px;
      }
      #customers tr:nth-child(even)
      {

      }
      #customers th {
                font-size:90%; width:500px; font-weight: bold; text-align:left; border: 1px solid #ddd; padding: 8px; color: #C73718
      }

      </style>
       ' || p_aciklama || '
       <table id="customers">
              <caption>
                      <b>' || p_baslik ||'</b>
              </caption>';

      RETURN html_table;

     -- background-color: #69f030;
   END INIT_TABLE;

   FUNCTION SUTUN_EKLE
   (
      p_sutun       IN LONG,
      text_sutunlar IN LONG
   ) RETURN LONG IS
      ress LONG := '';
   BEGIN
      ress := text_sutunlar ||
              '<th> '
              || p_sutun ||
               ' </th> ';
      RETURN ress;
   END SUTUN_EKLE;

   FUNCTION SUTUNLAR_EKLE
   (
      p_sutun_adlari IN string_list,
      text_sutunlar  IN LONG
   ) RETURN LONG IS
      ress LONG := '';
   BEGIN
      FOR i IN 1 .. p_sutun_adlari.COUNT LOOP
         ress := SUTUN_EKLE(p_sutun_adlari(i), ress);
      END LOOP;

      RETURN text_sutunlar || ress;
   END SUTUNLAR_EKLE;

   FUNCTION SATIR_EKLE
   (
      p_satir_values IN string_list,
      text_satirlar  IN LONG
   ) RETURN LONG IS
      ress LONG := '';
   BEGIN
      FOR i IN 1 .. p_satir_values.COUNT LOOP
         ress := ress || '<td>' || p_satir_values(i) || '</td>';
      END LOOP;
      ress := '
      <tr>
      ' || ress || '
      </tr>';
      RETURN text_satirlar || ress;
   END SATIR_EKLE;

   FUNCTION LENGTH_CHECK (sutunlar IN LONG, satirlar IN LONG,  MAX_LENGTH IN NUMBER DEFAULT 32000) RETURN BOOLEAN IS
     BEGIN

       RETURN (LENGTH(INIT_TABLE('', '')) + LENGTH(satirlar) + LENGTH(sutunlar) + 500) < MAX_LENGTH;
   END LENGTH_CHECK;


   FUNCTION BUILD_AND_GET_HTML_TABLE
   (
      p_baslik      IN LONG,
      p_aciklama    IN LONG,
      text_sutunlar IN LONG,
      text_satirlar IN LONG
   ) RETURN LONG IS
      html_table LONG(32760);
   BEGIN

      html_table := INIT_TABLE(p_baslik, p_aciklama);

      html_table := html_table  || '<tr>' || text_sutunlar || '</tr>' || text_satirlar || '
      </table>';

      RETURN html_table;
   END BUILD_AND_GET_HTML_TABLE;

   PROCEDURE TEST IS
      sutunlarHTML LONG := '';
      satirlarHTML LONG := '';

      ress LONG := '';
   BEGIN

      --SUTUN EKLEME

      sutunlarHTML := HTML_TABLE_API.SUTUNLAR_EKLE(HTML_TABLE_API.string_list('value1','value2','value3', 'value4', 'value5'),sutunlarHTML);

      --VEYA--

      sutunlarHTML := HTML_TABLE_API.SUTUN_EKLE('SUTUN1', sutunlarHTML);
      sutunlarHTML := HTML_TABLE_API.SUTUN_EKLE('SUTUN2', sutunlarHTML);
      sutunlarHTML := HTML_TABLE_API.SUTUN_EKLE('SUTUN3', sutunlarHTML);
      sutunlarHTML := HTML_TABLE_API.SUTUN_EKLE('SUTUN4', sutunlarHTML);
      sutunlarHTML := HTML_TABLE_API.SUTUN_EKLE('SUTUN5', sutunlarHTML);

      --SATIR EKLEME -- Not: Sutun say�s� kadar deger �ceren bir string_list verilmelidir.

      satirlarHTML := HTML_TABLE_API.SATIR_EKLE(HTML_TABLE_API.string_list('value1', 'value2', 'value3', 'value4','value5'), satirlarHTML);
      satirlarHTML := HTML_TABLE_API.SATIR_EKLE(HTML_TABLE_API.string_list('value1', 'value2', 'value3', 'value4','value5'), satirlarHTML);
      satirlarHTML := HTML_TABLE_API.SATIR_EKLE(HTML_TABLE_API.string_list('value1', 'value2', 'value3', 'value4','value5'), satirlarHTML);
      satirlarHTML := HTML_TABLE_API.SATIR_EKLE(HTML_TABLE_API.string_list('value1', 'value2', 'value3', 'value4','value5'), satirlarHTML);
      satirlarHTML := HTML_TABLE_API.SATIR_EKLE(HTML_TABLE_API.string_list('value1', 'value2', 'value3', 'value4','value5'), satirlarHTML);
      satirlarHTML := HTML_TABLE_API.SATIR_EKLE(HTML_TABLE_API.string_list('value1', 'value2', 'value3', 'value4','value5'), satirlarHTML);

      -- Ana HTML tabloyu olsuturacak k�s�m.
      ress := HTML_TABLE_API.BUILD_AND_GET_HTML_TABLE(p_baslik      => 'ORNEK TABLO', p_aciklama => '<br> ACIKLAMA BURAYA GELECEK! <br> Ama buraya da gelebilir.',
                                              text_sutunlar => sutunlarHTML,
                                              text_satirlar => satirlarHTML);

      dbms_output.put_line(ress);

   END;




END HTML_TABLE_API2;
/
