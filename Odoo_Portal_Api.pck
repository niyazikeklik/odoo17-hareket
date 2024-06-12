CREATE OR REPLACE PACKAGE Odoo_Portal_Api IS

FUNCTION Get_Emp_Org_Code(company_id_ varchar2, emp_no_ varchar2) return varchar2;

FUNCTION Get_Sup_Emp_no(company_id_ VARCHAR2, emp_no_ varchar2) return varchar2;

procedure Portal_Send_Pur_Ord(order_no_ varchar2, check_ number default 0);

PROCEDURE approve_sas(order_no_ varchar2, change_order_no_ varchar2, sequence_no_ number);

PROCEDURE reject_sas(order_no_ varchar2, change_order_no_ varchar2, sequence_no_ number, reject_code_ varchar2, reject_reason_ varchar2);

Procedure masraf_detay_ekle(detay_ varchar2);

Procedure masraf_detay_sil(detay_ varchar2);

PROCEDURE masraf_kdv(company_ VARCHAR2, kdv_orani_ number);

Procedure masraf_kdv_sil(company_ VARCHAR2, kdv_orani_ number);

PROCEDURE masraf_ongrup(ongrup_kodu_ VARCHAR2);

Procedure masraf_ongrup_sil(ongrup_kodu_ VARCHAR2);

PROCEDURE masraf_turu(masraf_turu_kodu_ VARCHAR2);

Procedure masraf_turu_sil(masraf_turu_kodu_ VARCHAR2);

PROCEDURE muhasebe_kodu(company_ VARCHAR2, code_part_ varchar2, code_part_value_ varchar2);

PROCEDURE muhasebe_kodu_sil(company_ VARCHAR2, code_part_ varchar2, code_part_value_ varchar2);

PROCEDURE aktivite(activity_seq_ number);

Procedure aktivite_sil(activity_seq_ number);

PROCEDURE proje(project_id_ varchar2);

PROCEDURE proje_sil(project_id_ varchar2);

FUNCTION Get_Emp_Bolum_For_Talep (
  company_ IN VARCHAR2, 
  emp_no_ VARCHAR2 ) RETURN VARCHAR2;
  
PROCEDURE nakit_hesap(company_ varchar2, short_name_ VARCHAR2);

Procedure nakit_hesap_sil(company_ varchar2, short_name_ varchar2);

procedure para_sil_ifs2_odoo(talep_id_ varchar2);

procedure para_satir_sil_ifs2_odoo(talep_id_ varchar2, satir_no_ number);

procedure masraf_sil_ifs2_odoo(masraf_no_ varchar2);

procedure masraf_satir_sil_ifs2_odoo(masraf_no_ varchar2, satir_no_ number);
  
PROCEDURE para_talebi_odoo2_ifs(
  company_id_         IN     VARCHAR2,
  talep_eden_id_      IN     VARCHAR2,
  talep_tarihi_       IN     DATE,
  bolum_              IN     VARCHAR2,
  notlar_             IN     VARCHAR2,
  currency_           IN     VARCHAR2,
  proje_              IN     VARCHAR2,
  proje_turu_         IN     VARCHAR2,
  durum_              IN     VARCHAR2,
  ref_talep_          IN     VARCHAR2,
  details_            IN     CLOB,
  para_talep_no_      IN OUT VARCHAR2);
  

PROCEDURE para_talebi_onay_odoo2_ifs(
  talep_id_ VARCHAR2,
  line_no_ number,
  step_no_ number,
  approval_status_db_ varchar2 default 'APP',
  note_ varchar2 default null);
  
procedure para_ifs2_odoo(talep_id_ varchar2);
procedure para_satir_ifs2_odoo(talep_id_ varchar2, satir_no_ number);

PROCEDURE masraf_odoo2_ifs(
  company_id_         IN     VARCHAR2,
  user_id_            IN     VARCHAR2,
  bolum_              IN     VARCHAR2,
  notlar_             IN     VARCHAR2,
  currency_           IN     VARCHAR2,
  durum_              IN     VARCHAR2,
  details_            IN     CLOB,
  masraf_no_          IN     OUT VARCHAR2);
  
procedure masraf_ifs2_odoo(masraf_no_ varchar2);
procedure masraf_satir_ifs2_odoo(masraf_no_ varchar2, line_no_ number);

PROCEDURE masraf_sil_odoo2_ifs(masraf_no_ varchar2);

PROCEDURE masraf_satir_sil_odoo2_ifs(masraf_no_ varchar2, satir_no_ number);

PROCEDURE para_sil_odoo2_ifs(talep_id_ varchar2);

PROCEDURE para_satir_sil_odoo2_ifs(talep_id_ varchar2, line_no_ number);

PROCEDURE Dokuman_Ekle (
   doc_title_ IN VARCHAR2,
   doc_no_ IN OUT VARCHAR2,
   doc_sheet_ IN OUT VARCHAR2,
   doc_rev_ IN OUT VARCHAR2,
   file_name_ IN OUT VARCHAR2,
   ext_ IN VARCHAR2,
   lu_name_ IN VARCHAR2,
   key_ref_ IN VARCHAR2 );
   
PROCEDURE Dokuman_Sil(
   file_name_ IN  VARCHAR2,
   lu_name_ IN VARCHAR2,
   key_ref_ IN VARCHAR2);


PROCEDURE Para_Talebi_Set_Iptal(Talep_id_ IN VARCHAR2 );

PROCEDURE Masraf_Set_Yayinlandi(Masraf_No_ IN VARCHAR2 );

PROCEDURE Masraf_Set_Iptal(Masraf_No_ IN VARCHAR2 );

PROCEDURE Init;

END Odoo_Portal_Api;
/
CREATE OR REPLACE PACKAGE BODY Odoo_Portal_Api IS

-----------------------------------------------------------------------------
-------------------- PRIVATE DECLARATIONS -----------------------------------
-----------------------------------------------------------------------------


-----------------------------------------------------------------------------
-------------------- LU SPECIFIC PUBLIC METHODS -----------------------------
-----------------------------------------------------------------------------
FUNCTION Get_Emp_Org_Code(company_id_ varchar2, emp_no_ varchar2) return varchar2
  IS
    pos_code_ varchar2(20);
  BEGIN
    return company_pers_assign_api.Get_Emp_Org_Code(company_id_, emp_no_);
  END Get_Emp_Org_Code;
  
  FUNCTION Get_Sup_Emp_no(company_id_ VARCHAR2, emp_no_ varchar2) return varchar2
  IS
    sup_emp_no_ varchar2(20);
  BEGIN
    for  rec_ in(select * from table(company_pers_assign_api.Get_Sup_Emp_Code(2025,
company_pers_assign_api.Get_Emp_Org_Code(company_id_, emp_no_),
company_pers_assign_api.Get_Emp_Pos_Code(company_id_, emp_no_))) where rownum=1) loop
      sup_emp_no_ := rec_.sup_emp_no_;
   end loop;
   return sup_emp_no_;
  END Get_Sup_Emp_no;
  
procedure Portal_Send_Pur_Ord(order_no_ varchar2, check_ number default 0)
IS
     http_req      utl_http.req;
     http_resp     utl_http.resp;
     json_request_  VARCHAR2(32767);
     v_len number;
     v_txt Varchar2(32767);
     json_response  CLOB;
     a_ varchar2(32767);
     result_ varchar2(32767);
     result_id_ number;
     request_id_ number;
     req_ varchar2(32767) := '';
     lines_ varchar2(32767):=''; 
     histories_ varchar2(32767) := '';
     approvers_ varchar2(32767) := '';
     files_ varchar2(32767) := '';
     temp_ varchar2(32767);
     req_id_ number;
     last_line_no_ number; 
     extra_satir_sayisi_ number := 0;
     proje_ varchar2(2000);  
     total_price_ number := 0;
     gross_total_price_ number := 0;   
     total1_ number := 0;
     total2_ number := 0;      
     date_approved_line_ varchar2(100);
     date_revoked_line_    varchar2(100); 
     chg_order_ number := 0;  
BEGIN 
     for rec_ in(select po.order_no, po.chg_order_no, line_no, release_no, part_no, pol.description description, buy_unit_meas, pol.new_qty quantity,
       pol.new_fbuy_unit_price*(100-new_discount)/100 fbuy_unit_price,
       (pol.new_fbuy_unit_price*(100-new_discount)/100)*new_qty total_price,
       (pol.new_fbuy_unit_price*(100-new_discount)/100)*pol.new_qty + pol.tax_amount gross_total_price,
       activity_api.get_activity_no(activity_seq) aktivite_no, 
       activity_api.Get_Description(activity_seq) aktivite_adi,
        activity_api.Get_Sub_Project_Id(activity_seq) alt_proje_no,
        sub_project_api.Get_Description(pol.project_id,activity_api.Get_Sub_Project_Id(activity_seq)) alt_proje_adi,
        pol.note_text notlar, po.rowstate
       from purch_chg_ord_line_tab pol, purch_chg_ord_tab po
        where   po.order_no = pol.order_no
        and po.chg_order_no = pol.chg_order_no
        and po.rowstate = 'Released'
        and po.order_no = order_no_) LOOP
         chg_order_ := 1;
         --pur_req_lines_.append(pljson('{"line_no": '||rec_.line_no||}', "release_no":'||rec_.release_no||',"part_no"="'||rec_.part_no||'","description"="'||rec_.description||'","buy_unit_meas"="'||rec_.buy_unit_meas||'","quantity"='||rec_.quantity||'}').to_json_value);
         if lines_ is null or length(lines_)<25000 THEN
           lines_ := lines_ ||'{
"baslik_id": 0, 
"line_no": '||rec_.line_no||', 
"release_no":'||rec_.release_no||',
"aktivite_no":"'||replace(replace(replace(replace(replace(rec_.aktivite_no,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'",
"aktivite_adi":"'||replace(replace(replace(replace(replace(rec_.aktivite_adi,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'",
"alt_proje_no":"'||replace(replace(replace(replace(replace(rec_.alt_proje_no,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'",
"alt_proje_adi":"'||replace(replace(replace(replace(replace(rec_.alt_proje_adi,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'",
"part_no":"'||rec_.part_no||'",
"description":"'||replace(replace(replace(replace(replace(rec_.description,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'",
"buy_unit_meas":"'||rec_.buy_unit_meas||'",
"notlar":"'||replace(replace(replace(replace(replace(rec_.notlar,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'",
"unit_price":"'||replace(rec_.fbuy_unit_price,',','.')||'",
"total_price":"'||replace(rec_.total_price,',','.')||'",
"gross_total_price":"'||replace(rec_.gross_total_price,',','.')||'",
"quantity":'||replace(to_char(rec_.quantity),',','.')||
'},';                                                                
           
           last_line_no_ := rec_.line_no;
         else
           extra_satir_sayisi_ := extra_satir_sayisi_ + 1;
           total_price_ := total_price_ + rec_.total_price;
           gross_total_price_ := gross_total_price_ + rec_.total_price;
         end if;
         total1_ := total1_ + rec_.total_price;
         total2_ := total2_ + rec_.gross_total_price;
     END LOOP;
     if chg_order_ = 0 THEN
       for rec_ in(select line_no, release_no, part_no, pol.description description, buy_unit_meas, buy_qty_due quantity,
         fbuy_unit_price*(100-discount)/100 fbuy_unit_price,
         (fbuy_unit_price*(100-discount)/100)*buy_qty_due total_price,
         (fbuy_unit_price*(100-discount)/100)*pol.buy_qty_due + pol.tax_amount gross_total_price,
         activity_api.get_activity_no(activity_seq) aktivite_no, 
         activity_api.Get_Description(activity_seq) aktivite_adi,
          activity_api.Get_Sub_Project_Id(activity_seq) alt_proje_no,
          sub_project_api.Get_Description(pol.project_id,activity_api.Get_Sub_Project_Id(activity_seq)) alt_proje_adi,
          pol.note_text notlar
         from ifsapp.purchase_order_line_tab pol where pol.order_no = order_no_) LOOP
              --dbms_output.put_line('test');
           --pur_req_lines_.append(pljson('{"line_no": '||rec_.line_no||}', "release_no":'||rec_.release_no||',"part_no"="'||rec_.part_no||'","description"="'||rec_.description||'","buy_unit_meas"="'||rec_.buy_unit_meas||'","quantity"='||rec_.quantity||'}').to_json_value);
           if lines_ is null or length(lines_)<25000 THEN
             lines_ := lines_ ||'{
  "baslik_id": 0, 
  "line_no": '||rec_.line_no||', 
  "release_no":'||rec_.release_no||',
  "aktivite_no":"'||replace(replace(replace(replace(replace(rec_.aktivite_no,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'",
  "aktivite_adi":"'||replace(replace(replace(replace(replace(rec_.aktivite_adi,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'",
  "alt_proje_no":"'||replace(replace(replace(replace(replace(rec_.alt_proje_no,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'",
  "alt_proje_adi":"'||replace(replace(replace(replace(replace(rec_.alt_proje_adi,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'",
  "part_no":"'||rec_.part_no||'",
  "description":"'||replace(replace(replace(replace(replace(rec_.description,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'",
  "buy_unit_meas":"'||rec_.buy_unit_meas||'",
  "notlar":"'||replace(replace(replace(replace(replace(rec_.notlar,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'",
  "unit_price":"'||replace(rec_.fbuy_unit_price,',','.')||'",
  "total_price":"'||replace(rec_.total_price,',','.')||'",
  "gross_total_price":"'||replace(rec_.gross_total_price,',','.')||'",
  "quantity":'||replace(to_char(rec_.quantity),',','.')||
  '},';                                                                
             
             last_line_no_ := rec_.line_no;
           else
             extra_satir_sayisi_ := extra_satir_sayisi_ + 1;
             total_price_ := total_price_ + rec_.total_price;
             gross_total_price_ := gross_total_price_ + rec_.total_price;
           end if;
           total1_ := total1_ + rec_.total_price;
           total2_ := total2_ + rec_.gross_total_price;
       END LOOP;
     END IF;
     if extra_satir_sayisi_ > 0 THEN
         lines_ := lines_ ||'{
"baslik_id": 0, 
"line_no": 9999, 
"release_no":0,
"part_no":"",
"description":"+'||extra_satir_sayisi_||' satýr daha kayýt mevcut lütfen talebi IFSden kontrol ediniz",
"buy_unit_meas":"X",
"unit_price":"'||replace(total_price_,',','.')||'",
"total_price":"'||replace(total_price_,',','.')||'",
"gross_total_price":"'||gross_total_price_||'",
"quantity":1
}';                    
     END IF;
     
     if lines_ like '%,' then
       lines_ := substr(lines_,1,length(lines_)-1);
     end if;
     lines_ := replace(lines_,'"quantity":.','"quantity":0.');
     for rec_ in(select pr.route,pr.sequence_no, pr.approval_rule, pr.approver_sign,
       pr.date_approved,revoked_signature_id revoked_sign,revoked_date,authorize_id,
       person_info_api.get_name(authorize_id) authorize_name, pr.chg_order_no
         from ifsapp.purchase_order_approval pr where pr.order_no = order_no_
         and nvl(purch_chg_ord_api.Get_Objstate(order_no_,pr.chg_order_no),'*') != 'Cancelled') LOOP
         --pur_req_lines_.append(pljson('{"line_no": '||rec_.line_no||}', "release_no":'||rec_.release_no||',"part_no"="'||rec_.part_no||'","description"="'||rec_.description||'","buy_unit_meas"="'||rec_.buy_unit_meas||'","quantity"='||rec_.quantity||'}').to_json_value);
         if rec_.date_approved is not null then
           date_approved_line_ := '"date_approved":"'||to_char(rec_.date_approved,'yyyy-MM-dd hh24:mi:ss')||'",';
         else
           date_approved_line_ := '';
         end if;
         if rec_.revoked_date is not null then
         
           date_revoked_line_ := '"date_revoked":"'||to_char(rec_.revoked_date,'yyyy-MM-dd hh24:mi:ss')||'",';
         else
           date_revoked_line_ := '';
         end if;
         histories_ := histories_ ||'{
         "baslik_id": 0, 
         "change_order_no": "'||rec_.chg_order_no||'",
         "sequence_no": '||rec_.sequence_no||', 
         "route": '||rec_.route||', 
         "approval_rule":"'||rec_.approval_rule||'",
         "approver_sign":"'||rec_.approver_sign||'",'||
         date_approved_line_||'
         "revoked_sign":"'||rec_.revoked_sign||'",'||
         date_revoked_line_||'
         "authorize_id":"'||rec_.authorize_id||'",
         "authorize_name":"'||rec_.authorize_name||'"
         },';
     END LOOP;
     if histories_ like '%,' then
       histories_ := substr(histories_,1,length(histories_)-1);
     end if;
     
     for rec_ in(select i.doc_class,
         i.doc_no,
         i.doc_sheet,
         i.doc_rev,
         i.user_created,
         t.title,
         e.file_name,
         e.path,
         e.file_type
         from doc_reference_object_tab o, doc_issue_tab i,
         doc_title_tab t,
         edm_file_tab e
          where o.lu_name = 'PurchaseOrder' and key_ref= 'ORDER_NO='||order_no_||'^'
        and o.doc_class = i.doc_class and o.doc_no = i.doc_no
        and o.doc_sheet = i.doc_sheet
        and o.doc_rev = i.doc_rev
        and i.doc_class = t.doc_class
        and i.doc_no = t.doc_no
        and i.doc_class = e.doc_class
        and i.doc_no = e.doc_no
        and i.doc_sheet = e.doc_sheet
        and i.doc_rev = e.doc_rev
        and e.doc_type = 'ORIGINAL') 
     LOOP
         --pur_req_lines_.append(pljson('{"line_no": '||rec_.line_no||}', "release_no":'||rec_.release_no||',"part_no"="'||rec_.part_no||'","description"="'||rec_.description||'","buy_unit_meas"="'||rec_.buy_unit_meas||'","quantity"='||rec_.quantity||'}').to_json_value);
         files_ := files_ ||'{
         "baslik_id": 0, 
         "user_created": "'||rec_.user_created||'", 
         "title":"'||rec_.title||'",
         "file_name":"'||rec_.file_name||'",
         "path":"'||replace(rec_.path,'\','\\')||'",
         "file_type":"'||rec_.file_type||'"
         },';
     END LOOP;
     if files_ like '%,' then
       files_ := substr(files_,1,length(files_)-1);
     end if;
     --json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["PROD",2,"080808","tr.purch_req","create_all",['||req_||'], ['||lines_||'],[],[]]}}';       
      dbms_output.put_line('AAAAA');
      
      for rec_ in(select order_no, vendor_no, supplier_info_api.get_name(vendor_no) tedarikci_adi,
        contract, PURCHASE_ORDER_TYPE_API.Get_Description( ORDER_CODE ) order_code,WANTED_RECEIPT_DATE ,
        HARKT_PURCH_ORDER_TYPE_API.GET_DESCRIPTION(ORDER_TYPE) order_type,
        currency_code, person_info_api.Get_Name(buyer_code) purchase_buyer, person_info_api.Get_Name(a.AUTHORIZE_CODE) coordinator,  a.rowstate state,
        a.project_id proje_no,
        project_api.get_name(a.project_id) proje_adi, 
        nvl(b.cf$_note_text,a.note_text) note_text
         from purchase_order_tab a, purchase_order_cft b where a.order_no = order_no_ and a.rowkey=b.rowkey(+)) LOOP
         dbms_output.put_line(length(lines_));
         dbms_output.put_line(length(histories_));
         dbms_output.put_line(length(files_));
        req_ := '
        {
          "order_no": "'||rec_.order_no||'",
          "vendor_no": "'||rec_.vendor_no||'",
          "vendor_name":"'||rec_.tedarikci_adi||'",
          "site":"'||rec_.contract||'",
          "order_code":"'||rec_.order_code||'",
          "order_type":"'||rec_.order_type||'",
          "delivery_date": "'||to_char(rec_.WANTED_RECEIPT_DATE,'yyyy-MM-dd hh24:mi:ss')||'",
          "currency_code":"'||rec_.currency_code||'",
          "purchase_buyer":"'||rec_.purchase_buyer||'",
          "coordinator":"'||rec_.coordinator||'",
          "total_price":"'||replace(total1_,',','.')||'",
          "gross_total_price":"'||replace(total2_,',','.')||'",
          "proje_no":"'||rec_.proje_no||'",
          "proje_adi":"'||replace(replace(replace(replace(replace(rec_.proje_adi,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'",
          "state":"'||rec_.state||'",
          "notlar":"'||replace(replace(replace(replace(replace(rec_.note_text,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'",
          "satir_ids":['||lines_||'], 
          "onay_ids":['||histories_||'],
          "doc_ids":['||files_||']
        }';
        dbms_output.put_line('test2');
     END LOOP;
     if req_ is null then
       req_ := '{ "order_no":"'||order_no_||'",
          "satir_ids":[], 
          "onay_ids":[],
          "doc_ids":[],
          "state":"Closed"
       }';
     end if;

     dbms_output.put_line('1111');
     for rec_ in(select * from odoo_portal_param_tab where param_name='ODOO_SERVER') loop
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","sas.baslik","create_or_write_all",['||req_||','||check_||']]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       dbms_output.put_line(json_request_);
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    --'http://10.0.0.77:8070/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
     end loop;
     dbms_output.put_line('3');
     
     UTL_HTTP.SET_BODY_CHARSET('UTF-8');
     UTL_HTTP.set_header(http_req, 'Connection', 'close');
     UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
     UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
     UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
      dbms_output.put_line('4');
      http_resp := UTL_HTTP.get_response(http_req);
       dbms_output.put_line('5');
     utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
     json_response := null;
     dbms_output.put_line('Ýstek');
      dbms_output.put_line(json_request_);
     FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
     LOOP
         utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
         json_response := json_response || v_txt; -- build up CLOB
     END LOOP;
     utl_http.end_response(http_resp);
     dbms_output.put_line('Dönüþ');
     dbms_output.put_line(json_response);
EXCEPTION WHEN OTHERS THEN
      NULL;
END Portal_Send_Pur_Ord;


PROCEDURE approve_sas(order_no_ varchar2, change_order_no_ varchar2, sequence_no_ number) IS
  site_ varchar2(20);
  cnt_ NUMBER := 0;
  hata_ varchar2(2000);
BEGIN
  site_ := purchase_order_api.Get_Contract(order_no_);
  select count(1) INTO cnt_ from user_allowed_site_tab s where s.userid = fnd_session_api.Get_Fnd_User() and s.contract = site_;
  IF cnt_ = 0 THEN
    
    error_sys.system_general('<hata>Sipariþ onaylanamadý. '||site_||' sitesine yetkiniz yoktur, sistem yöneticinizle iletiþime geçiniz.</hata>');
  END IF;
  for rec_ in(select * from purchase_order_approval_tab a where a.order_no = order_no_ and a.chg_order_no = change_order_no_ 
    and a.sequence_no= sequence_no_ and rownum=1) loop
    begin
      IFSAPP.Purchase_Order_Approval_API.Authorize(rec_.order_no,
      rec_.chg_order_no,rec_.sequence_no,rec_.company,rec_.authorize_id,rec_.authorize_group_id,rec_.project_role_id,
      rec_.pos_code,rec_.org_code,rec_.buyer_code);
    end;
    --Portal_Send_Pur_ord(rec_.order_no);
  end loop;
END approve_sas;

PROCEDURE reject_sas(order_no_ varchar2, change_order_no_ varchar2, sequence_no_ number, reject_code_ varchar2, reject_reason_ varchar2) IS
  girdi_ number := 0;
  site_ varchar2(20);
  company_ varchar2(20);
  cnt_ NUMBER := 0;
BEGIN
  site_ := purchase_order_api.Get_Contract(order_no_);
  company_ := site_api.get_company(site_);
  select count(1) INTO cnt_ from  PUR_AUTH_REJECT_REASON p where p.company = company_ and p.reject_reason_id = reject_code_;
  IF cnt_ = 0 THEN
    Error_sys.system_general('<hata>Hata kodu '||reject_code_||', '||company_||' þirketinde tanýmlý deðil, lütfen sistem yöneticinizle iletiþime geçiniz.</hata>');
  END IF;
  select count(1) INTO cnt_ from user_allowed_site_tab s where s.userid = fnd_session_api.Get_Fnd_User() and s.contract = site_;
  IF cnt_ = 0 THEN
    error_sys.system_general('<hata>Sipariþ reddedilemedi. '||site_||' sitesine yetkiniz yoktur, sistem yöneticinizle iletiþime geçiniz.</hata>');
  END IF;
 for rec_ in(select * from purchase_order_approval a where a.order_no = order_no_ and a.chg_order_no = change_order_no_ 
   and a.sequence_no = sequence_no_ and rownum=1) loop
   begin
     IFSAPP.Purchase_Order_Approval_API.Reject_Authorization(rec_.order_no,
     rec_.chg_order_no, rec_.sequence_no, reject_code_, reject_reason_);
   exception when others then
     error_sys.system_general('<hata>Sipariþ reddedilemedi. Lütfen sistem yöneticinizle iletiþime geçiniz.</hata>');
   end;
   --Portal_Send_Pur_ord(rec_.order_no);
 end loop;
END reject_sas;

Procedure masraf_detay_ekle(detay_ varchar2) 
IS
  http_req      utl_http.req;
  http_resp     utl_http.resp;
  json_request_  VARCHAR2(32767);
  req_ varchar2(32767) := '';
  v_len NUMBER;
  json_response varchar2(32767);
  v_txt varchar2(32767);
BEGIN
  FOR rec_ IN(select * from odoo_portal_param_tab where param_name='ODOO_SERVER') LOOP
       req_ := '
        {
          "name": "'||detay_||'"
        }';
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","harkt.detay","create",['||req_||']]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    --'http://10.0.0.77:8070/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
   end loop;
   dbms_output.put_line('3');
   UTL_HTTP.SET_BODY_CHARSET('UTF-8');
   UTL_HTTP.set_header(http_req, 'Connection', 'close');
   UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
   UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
   UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
    dbms_output.put_line('4');
    http_resp := UTL_HTTP.get_response(http_req);
     dbms_output.put_line('5');
   utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
   json_response := null;
   dbms_output.put_line('Ýstek');
    dbms_output.put_line(json_request_);
   FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
   LOOP
       utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
       json_response := json_response || v_txt; -- build up CLOB
   END LOOP;
   utl_http.end_response(http_resp);
   dbms_output.put_line('Dönüþ');
   dbms_output.put_line(json_response);
END masraf_detay_ekle;


Procedure masraf_detay_sil(detay_ varchar2) 
IS
  http_req      utl_http.req;
  http_resp     utl_http.resp;
  json_request_  VARCHAR2(32767);
  req_ varchar2(32767) := '';
  v_len NUMBER;
  json_response varchar2(32767);
  v_txt varchar2(32767);
BEGIN
  FOR rec_ IN(select * from odoo_portal_param_tab where param_name='ODOO_SERVER') LOOP
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","harkt.detay","delete",["name", "'||detay_||'"]]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    --'http://10.0.0.77:8070/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
   end loop;
   dbms_output.put_line('3');
   UTL_HTTP.SET_BODY_CHARSET('UTF-8');
   UTL_HTTP.set_header(http_req, 'Connection', 'close');
   UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
   UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
   UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
    dbms_output.put_line('4');
    http_resp := UTL_HTTP.get_response(http_req);
     dbms_output.put_line('5');
   utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
   json_response := null;
   dbms_output.put_line('Ýstek');
    dbms_output.put_line(json_request_);
   FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
   LOOP
       utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
       json_response := json_response || v_txt; -- build up CLOB
   END LOOP;
   utl_http.end_response(http_resp);
   dbms_output.put_line('Dönüþ');
   dbms_output.put_line(json_response);
END masraf_detay_sil;


PROCEDURE masraf_kdv(company_ VARCHAR2, kdv_orani_ number) 
IS
  http_req      utl_http.req;
  http_resp     utl_http.resp;
  json_request_  VARCHAR2(32767);
  req_ varchar2(32767) := '';
  v_len NUMBER;
  json_response varchar2(32767);
  v_txt varchar2(32767);
BEGIN
  FOR rec_ IN(select * from odoo_portal_param_tab where param_name='ODOO_SERVER') LOOP
       req_ := '
        {
          "company": "'|| company_||'",
          "kdv_orani": "'|| kdv_orani_||'",
          "kdv_kodu": "'|| harkt_kdv_kodlari_api.Get_Kdv_Kodu(kdv_orani_, company_)||'",
          "vergi_kodu": "'|| harkt_kdv_kodlari_api.Get_Vergi_Kodu(kdv_orani_, company_)||'"
        }';
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","harkt.kdv","write_or_create",['||req_||']]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    --'http://10.0.0.77:8070/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
   end loop;
   dbms_output.put_line('3');
   UTL_HTTP.SET_BODY_CHARSET('UTF-8');
   UTL_HTTP.set_header(http_req, 'Connection', 'close');
   UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
   UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
   UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
    dbms_output.put_line('4');
    http_resp := UTL_HTTP.get_response(http_req);
     dbms_output.put_line('5');
   utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
   json_response := null;
   dbms_output.put_line('Ýstek');
    dbms_output.put_line(json_request_);
   FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
   LOOP
       utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
       json_response := json_response || v_txt; -- build up CLOB
   END LOOP;
   utl_http.end_response(http_resp);
   dbms_output.put_line('Dönüþ');
   dbms_output.put_line(json_response);
END masraf_kdv;


Procedure masraf_kdv_sil(company_ VARCHAR2, kdv_orani_ number) 
IS
  http_req      utl_http.req;
  http_resp     utl_http.resp;
  json_request_  VARCHAR2(32767);
  req_ varchar2(32767) := '';
  v_len NUMBER;
  json_response varchar2(32767);
  v_txt varchar2(32767);
BEGIN
  FOR rec_ IN(select * from odoo_portal_param_tab where param_name='ODOO_SERVER') LOOP
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","harkt.kdv","delete",["company", "'||company_||'","kdv_orani", '||kdv_orani_||']]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    --'http://10.0.0.77:8070/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
   end loop;
   dbms_output.put_line('3');
   UTL_HTTP.SET_BODY_CHARSET('UTF-8');
   UTL_HTTP.set_header(http_req, 'Connection', 'close');
   UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
   UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
   UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
    dbms_output.put_line('4');
    http_resp := UTL_HTTP.get_response(http_req);
     dbms_output.put_line('5');
   utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
   json_response := null;
   dbms_output.put_line('Ýstek');
    dbms_output.put_line(json_request_);
   FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
   LOOP
       utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
       json_response := json_response || v_txt; -- build up CLOB
   END LOOP;
   utl_http.end_response(http_resp);
   dbms_output.put_line('Dönüþ');
   dbms_output.put_line(json_response);
END masraf_kdv_sil;


PROCEDURE masraf_ongrup(ongrup_kodu_ VARCHAR2) 
IS
  http_req      utl_http.req;
  http_resp     utl_http.resp;
  json_request_  VARCHAR2(32767);
  req_ varchar2(32767) := '';
  v_len NUMBER;
  json_response varchar2(32767);
  v_txt varchar2(32767);
BEGIN
  FOR rec_ IN(select * from odoo_portal_param_tab where param_name='ODOO_SERVER') LOOP
       req_ := '
        {
          "ongrup_kodu": "'|| ongrup_kodu_||'",
          "ongrup_adi": "'|| harkt_masraf_on_gruplar_api.Get_Masraf_On_Grup_Adi(ongrup_kodu_)||'"
        }';
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","harkt.masraf.ongrup","write_or_create",['||req_||']]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
   end loop;
   dbms_output.put_line('3');
   UTL_HTTP.SET_BODY_CHARSET('UTF-8');
   UTL_HTTP.set_header(http_req, 'Connection', 'close');
   UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
   UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
   UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
    dbms_output.put_line('4');
    http_resp := UTL_HTTP.get_response(http_req);
     dbms_output.put_line('5');
   utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
   json_response := null;
   dbms_output.put_line('Ýstek');
    dbms_output.put_line(json_request_);
   FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
   LOOP
       utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
       json_response := json_response || v_txt; -- build up CLOB
   END LOOP;
   utl_http.end_response(http_resp);
   dbms_output.put_line('Dönüþ');
   dbms_output.put_line(json_response);
END masraf_ongrup;


Procedure masraf_ongrup_sil(ongrup_kodu_ VARCHAR2) 
IS
  http_req      utl_http.req;
  http_resp     utl_http.resp;
  json_request_  VARCHAR2(32767);
  req_ varchar2(32767) := '';
  v_len NUMBER;
  json_response varchar2(32767);
  v_txt varchar2(32767);
BEGIN
  FOR rec_ IN(select * from odoo_portal_param_tab where param_name='ODOO_SERVER') LOOP
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","harkt.masraf.ongrup","delete",["ongrup_kodu", "'||ongrup_kodu_||'"]]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    --'http://10.0.0.77:8070/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
   end loop;
   dbms_output.put_line('3');
   UTL_HTTP.SET_BODY_CHARSET('UTF-8');
   UTL_HTTP.set_header(http_req, 'Connection', 'close');
   UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
   UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
   UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
    dbms_output.put_line('4');
    http_resp := UTL_HTTP.get_response(http_req);
     dbms_output.put_line('5');
   utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
   json_response := null;
   dbms_output.put_line('Ýstek');
    dbms_output.put_line(json_request_);
   FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
   LOOP
       utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
       json_response := json_response || v_txt; -- build up CLOB
   END LOOP;
   utl_http.end_response(http_resp);
   dbms_output.put_line('Dönüþ');
   dbms_output.put_line(json_response);
END masraf_ongrup_sil;


PROCEDURE masraf_turu(masraf_turu_kodu_ VARCHAR2) 
IS
  http_req      utl_http.req;
  http_resp     utl_http.resp;
  json_request_  VARCHAR2(32767);
  req_ varchar2(32767) := '';
  v_len NUMBER;
  json_response varchar2(32767);
  v_txt varchar2(32767);
BEGIN
  FOR rec_ IN(select p.*, h.* from odoo_portal_param_tab p, harkt_masraf_turleri_tab h where param_name='ODOO_SERVER' and h.masraf_turu_kodu=masraf_turu_kodu_) LOOP
       req_ := '
        {
          "masraf_turu_kodu": "'|| masraf_turu_kodu_||'",
          "company": "'|| rec_.company||'",
          "detay_kodu": "'|| rec_.detay_secenek||'",
          "ongrup_kodu": "'|| rec_.masraf_on_grup_kodu||'",
          "name": "'|| rec_.masraf_turu_adi||'",
          "satinalma_grup_kodu": "'|| rec_.satinalma_grubu||'",
          "satinalma_grup_adi": "'|| PURCHASE_PART_GROUP_API.Get_Description(rec_.satinalma_grubu)||'",
          "proje_zorunlu": "'|| rec_.proje_zorunlu||'",
          "detay_zorunlu": "'|| rec_.detay_zorunlu||'",
          "site_zorunlu": "'|| rec_.site_zorunlu||'",
          "bolge_zorunlu": "'|| rec_.bolge_zorunlu||'",
          "gider_cesidi_kodu": "'|| rec_.gider_cesidi_kodu||'",
          "gider_cesidi_adi": "'|| code_c_api.Get_Description(rec_.company, rec_.gider_cesidi_kodu)||'",
          "harcama_toleransi": "'|| rec_.harcama_toleransi||'"
        }';
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","harkt.masraf.turu","write_or_create",['||req_||']]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
   end loop;
   dbms_output.put_line('3');
   UTL_HTTP.SET_BODY_CHARSET('UTF-8');
   UTL_HTTP.set_header(http_req, 'Connection', 'close');
   UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
   UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
   UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
    dbms_output.put_line('4');
    http_resp := UTL_HTTP.get_response(http_req);
     dbms_output.put_line('5');
   utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
   json_response := null;
   dbms_output.put_line('Ýstek');
    dbms_output.put_line(json_request_);
   FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
   LOOP
       utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
       json_response := json_response || v_txt; -- build up CLOB
   END LOOP;
   utl_http.end_response(http_resp);
   dbms_output.put_line('Dönüþ');
   dbms_output.put_line(json_response);
END masraf_turu;

PROCEDURE masraf_turu_sil(masraf_turu_kodu_ VARCHAR2) 
IS
  http_req      utl_http.req;
  http_resp     utl_http.resp;
  json_request_  VARCHAR2(32767);
  req_ varchar2(32767) := '';
  v_len NUMBER;
  json_response varchar2(32767);
  v_txt varchar2(32767);
BEGIN
  FOR rec_ IN(select * from odoo_portal_param_tab where param_name='ODOO_SERVER') LOOP
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","harkt.masraf.turu","delete",["masraf_turu_kodu", "'||masraf_turu_kodu_||'"]]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    --'http://10.0.0.77:8070/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
   end loop;
   dbms_output.put_line('3');
   UTL_HTTP.SET_BODY_CHARSET('UTF-8');
   UTL_HTTP.set_header(http_req, 'Connection', 'close');
   UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
   UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
   UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
    dbms_output.put_line('4');
    http_resp := UTL_HTTP.get_response(http_req);
     dbms_output.put_line('5');
   utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
   json_response := null;
   dbms_output.put_line('Ýstek');
    dbms_output.put_line(json_request_);
   FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
   LOOP
       utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
       json_response := json_response || v_txt; -- build up CLOB
   END LOOP;
   utl_http.end_response(http_resp);
   dbms_output.put_line('Dönüþ');
   dbms_output.put_line(json_response);
END masraf_turu_sil;


PROCEDURE muhasebe_kodu(company_ VARCHAR2, code_part_ varchar2, code_part_value_ varchar2) 
IS
  http_req      utl_http.req;
  http_resp     utl_http.resp;
  json_request_  VARCHAR2(32767);
  req_ varchar2(32767) := '';
  v_len NUMBER;
  json_response varchar2(32767);
  v_txt varchar2(32767);
BEGIN
  FOR rec_ IN(select p.*, h.code_part, h.code_part_value, h.description, h.valid_from, h.valid_until, h.detay_secenek from odoo_portal_param_tab p, accounting_code_part_value_tab h 
    where param_name='ODOO_SERVER' 
    and h.company = company_ 
    and h.code_part = code_part_ 
    and h.code_part_value = code_part_value_
    and h.code_part in('B','F','H','J')) LOOP
       req_ := '
        {
          "company": "'|| company_||'",
          "kod_yapisi":"'||rec_.code_part||'",
          "code": "'|| rec_.code_part_value||'",
          "name": "'|| rec_.description||'",
          "detay_secenek": "'|| rec_.detay_secenek||'",
          "valid_from": "'|| to_char(rec_.valid_from,'yyyy-MM-dd hh24:mi:ss')||'",
          "valid_to": "'|| to_char(rec_.valid_until,'yyyy-MM-dd hh24:mi:ss')||'"
        }';
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","harkt.muhasebe.kodu","write_or_create",['||req_||']]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
   end loop;
   dbms_output.put_line('3');
   UTL_HTTP.SET_BODY_CHARSET('UTF-8');
   UTL_HTTP.set_header(http_req, 'Connection', 'close');
   UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
   UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
   UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
    dbms_output.put_line('4');
    http_resp := UTL_HTTP.get_response(http_req);
     dbms_output.put_line('5');
   utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
   json_response := null;
   dbms_output.put_line('Ýstek');
    dbms_output.put_line(json_request_);
   FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
   LOOP
       utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
       json_response := json_response || v_txt; -- build up CLOB
   END LOOP;
   utl_http.end_response(http_resp);
   dbms_output.put_line('Dönüþ');
   dbms_output.put_line(json_response);
END muhasebe_kodu;


PROCEDURE muhasebe_kodu_sil(company_ VARCHAR2, code_part_ varchar2, code_part_value_ varchar2) 
IS
  http_req      utl_http.req;
  http_resp     utl_http.resp;
  json_request_  VARCHAR2(32767);
  req_ varchar2(32767) := '';
  v_len NUMBER;
  json_response varchar2(32767);
  v_txt varchar2(32767);
BEGIN
  FOR rec_ IN(select * from odoo_portal_param_tab where param_name='ODOO_SERVER') LOOP
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","harkt.muhasebe.kodu","delete",["company", "'||company_||'","code_part", "'||code_part_||'","code_part_value", "'||code_part_value_||'"]]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    --'http://10.0.0.77:8070/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
   end loop;
   dbms_output.put_line('3');
   UTL_HTTP.SET_BODY_CHARSET('UTF-8');
   UTL_HTTP.set_header(http_req, 'Connection', 'close');
   UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
   UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
   UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
    dbms_output.put_line('4');
    http_resp := UTL_HTTP.get_response(http_req);
     dbms_output.put_line('5');
   utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
   json_response := null;
   dbms_output.put_line('Ýstek');
    dbms_output.put_line(json_request_);
   FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
   LOOP
       utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
       json_response := json_response || v_txt; -- build up CLOB
   END LOOP;
   utl_http.end_response(http_resp);
   dbms_output.put_line('Dönüþ');
   dbms_output.put_line(json_response);
END muhasebe_kodu_sil;


PROCEDURE proje(project_id_ varchar2) 
IS
  http_req      utl_http.req;
  http_resp     utl_http.resp;
  json_request_  VARCHAR2(32767);
  req_ varchar2(32767) := '';
  v_len NUMBER;
  json_response varchar2(32767);
  v_txt varchar2(32767);
BEGIN
  FOR rec_ IN(select o.*,a.name, a.rowstate, a.company from odoo_portal_param_tab o, project_tab a where param_name='ODOO_SERVER'
    and project_id = project_id_) LOOP
       req_ := '
        {
          "code": "'|| project_id_||'",
          "name": "'|| rec_.name||'",
          "state": "'|| rec_.rowstate||'",
          "company": "'|| rec_.company||'"
        }';
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","harkt.proje","write_or_create",['||req_||']]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
   end loop;
   dbms_output.put_line('3');
   UTL_HTTP.SET_BODY_CHARSET('UTF-8');
   UTL_HTTP.set_header(http_req, 'Connection', 'close');
   UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
   UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
   UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
    dbms_output.put_line('4');
    http_resp := UTL_HTTP.get_response(http_req);
     dbms_output.put_line('5');
   utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
   json_response := null;
   dbms_output.put_line('Ýstek');
    dbms_output.put_line(json_request_);
   FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
   LOOP
       utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
       json_response := json_response || v_txt; -- build up CLOB
   END LOOP;
   utl_http.end_response(http_resp);
   dbms_output.put_line('Dönüþ');
   dbms_output.put_line(json_response);
END proje;


Procedure proje_sil(project_id_ varchar2) 
IS
  http_req      utl_http.req;
  http_resp     utl_http.resp;
  json_request_  VARCHAR2(32767);
  req_ varchar2(32767) := '';
  v_len NUMBER;
  json_response varchar2(32767);
  v_txt varchar2(32767);
BEGIN
  FOR rec_ IN(select * from odoo_portal_param_tab where param_name='ODOO_SERVER') LOOP
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","harkt.proje","delete",["ongrup_kodu", "'||project_id_||'"]]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    --'http://10.0.0.77:8070/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
   end loop;
   dbms_output.put_line('3');
   UTL_HTTP.SET_BODY_CHARSET('UTF-8');
   UTL_HTTP.set_header(http_req, 'Connection', 'close');
   UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
   UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
   UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
    dbms_output.put_line('4');
    http_resp := UTL_HTTP.get_response(http_req);
     dbms_output.put_line('5');
   utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
   json_response := null;
   dbms_output.put_line('Ýstek');
    dbms_output.put_line(json_request_);
   FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
   LOOP
       utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
       json_response := json_response || v_txt; -- build up CLOB
   END LOOP;
   utl_http.end_response(http_resp);
   dbms_output.put_line('Dönüþ');
   dbms_output.put_line(json_response);
END proje_sil;

PROCEDURE aktivite(activity_seq_ number) 
IS
  http_req      utl_http.req;
  http_resp     utl_http.resp;
  json_request_  VARCHAR2(32767);
  req_ varchar2(32767) := '';
  v_len NUMBER;
  json_response varchar2(32767);
  v_txt varchar2(32767);
BEGIN
  FOR rec_ IN(select o.*,a.activity_seq, a.activity_no, a.description,
    a.sub_project_id, a.project_id from odoo_portal_param_tab o, activity_tab a where param_name='ODOO_SERVER'
    and activity_seq = activity_seq_) LOOP
       req_ := '
        {
          "activity_seq": "'|| activity_seq_||'",
          "activity_no": "'|| rec_.activity_no||'",
          "project": "'|| rec_.project_id||'",
          "sub_project_no": "'|| rec_.sub_project_id||'",
          "activity_name": "'|| rec_.description||'"
        }';
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","harkt.aktivite","write_or_create",['||req_||']]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
   end loop;
   dbms_output.put_line('3');
   UTL_HTTP.SET_BODY_CHARSET('UTF-8');
   UTL_HTTP.set_header(http_req, 'Connection', 'close');
   UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
   UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
   UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
    dbms_output.put_line('4');
    http_resp := UTL_HTTP.get_response(http_req);
     dbms_output.put_line('5');
   utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
   json_response := null;
   dbms_output.put_line('Ýstek');
    dbms_output.put_line(json_request_);
   FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
   LOOP
       utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
       json_response := json_response || v_txt; -- build up CLOB
   END LOOP;
   utl_http.end_response(http_resp);
   dbms_output.put_line('Dönüþ');
   dbms_output.put_line(json_response);
END aktivite;


Procedure aktivite_sil(activity_seq_ number) 
IS
  http_req      utl_http.req;
  http_resp     utl_http.resp;
  json_request_  VARCHAR2(32767);
  req_ varchar2(32767) := '';
  v_len NUMBER;
  json_response varchar2(32767);
  v_txt varchar2(32767);
BEGIN
  FOR rec_ IN(select * from odoo_portal_param_tab where param_name='ODOO_SERVER') LOOP
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","harkt.aktivite","delete",["activity_seq", "'||activity_seq_||'"]]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    --'http://10.0.0.77:8070/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
   end loop;
   dbms_output.put_line('3');
   UTL_HTTP.SET_BODY_CHARSET('UTF-8');
   UTL_HTTP.set_header(http_req, 'Connection', 'close');
   UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
   UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
   UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
    dbms_output.put_line('4');
    http_resp := UTL_HTTP.get_response(http_req);
     dbms_output.put_line('5');
   utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
   json_response := null;
   dbms_output.put_line('Ýstek');
    dbms_output.put_line(json_request_);
   FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
   LOOP
       utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
       json_response := json_response || v_txt; -- build up CLOB
   END LOOP;
   utl_http.end_response(http_resp);
   dbms_output.put_line('Dönüþ');
   dbms_output.put_line(json_response);
END aktivite_sil;


PROCEDURE nakit_hesap(company_ varchar2, short_name_ VARCHAR2) 
IS
  http_req      utl_http.req;
  http_resp     utl_http.resp;
  json_request_  VARCHAR2(32767);
  req_ varchar2(32767) := '';
  v_len NUMBER;
  json_response varchar2(32767);
  v_txt varchar2(32767);
BEGIN
  FOR rec_ IN(select o.*,a.short_name, a.company, a.description, a.account_identity account_no, a.account_reference, a.currency
     from odoo_portal_param_tab o, cash_account_tab a where param_name='ODOO_SERVER'
    and company = company_ and short_name = short_name_) LOOP
       req_ := '
        {
          "company": "'|| rec_.company||'",
          "name": "'|| rec_.short_name||'",
          "description": "'|| rec_.description||'",
          "account_no": "'|| rec_.account_no||'",
          "reference": "'|| rec_.account_reference||'",
          "currency": "'|| rec_.currency||'"
        }';
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","harkt.nakit.hesap","write_or_create",['||req_||']]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
   end loop;
   dbms_output.put_line('3');
   UTL_HTTP.SET_BODY_CHARSET('UTF-8');
   UTL_HTTP.set_header(http_req, 'Connection', 'close');
   UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
   UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
   UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
    dbms_output.put_line('4');
    http_resp := UTL_HTTP.get_response(http_req);
     dbms_output.put_line('5');
   utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
   json_response := null;
   dbms_output.put_line('Ýstek');
    dbms_output.put_line(json_request_);
   FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
   LOOP
       utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
       json_response := json_response || v_txt; -- build up CLOB
   END LOOP;
   utl_http.end_response(http_resp);
   dbms_output.put_line('Dönüþ');
   dbms_output.put_line(json_response);
END nakit_hesap;

Procedure nakit_hesap_sil(company_ varchar2, short_name_ varchar2) 
IS
  http_req      utl_http.req;
  http_resp     utl_http.resp;
  json_request_  VARCHAR2(32767);
  req_ varchar2(32767) := '';
  v_len NUMBER;
  json_response varchar2(32767);
  v_txt varchar2(32767);
BEGIN
  FOR rec_ IN(select * from odoo_portal_param_tab where param_name='ODOO_SERVER') LOOP
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","harkt.nakit.hesap","delete",["company", "'||company_||'","name", "'||short_name_||'"]]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    --'http://10.0.0.77:8070/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
   end loop;
   dbms_output.put_line('3');
   UTL_HTTP.SET_BODY_CHARSET('UTF-8');
   UTL_HTTP.set_header(http_req, 'Connection', 'close');
   UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
   UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
   UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
    dbms_output.put_line('4');
    http_resp := UTL_HTTP.get_response(http_req);
     dbms_output.put_line('5');
   utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
   json_response := null;
   dbms_output.put_line('Ýstek');
    dbms_output.put_line(json_request_);
   FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
   LOOP
       utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
       json_response := json_response || v_txt; -- build up CLOB
   END LOOP;
   utl_http.end_response(http_resp);
   dbms_output.put_line('Dönüþ');
   dbms_output.put_line(json_response);
END nakit_hesap_sil;

FUNCTION Get_Emp_Bolum_For_Talep (
  company_ IN VARCHAR2, 
  emp_no_ VARCHAR2 ) RETURN VARCHAR2
IS
  result_ varchar2(200);
  CURSOR Get_code_b_for_talep IS
   SELECT code_b_api.Get_Description(b.company, b.code_b) FROM trbrd_personel_sicil_tab b
   WHERE b.company = COMPANY_
   and   b.emp_no = emp_no_
   ORDER BY b.seq_no desc;        
BEGIN

   OPEN Get_code_b_for_talep;
   FETCH Get_code_b_for_talep INTO result_;
   CLOSE Get_code_b_for_talep;
         
   RETURN result_;
END Get_Emp_Bolum_For_Talep;


PROCEDURE masraf_sil_odoo2_ifs(masraf_no_ varchar2)
IS
   key_ VARCHAR2(2000);
   
   CURSOR Line_Exists IS
   SELECT COUNT(*)
    FROM harkt_masraf_giris_line l
   WHERE l.masraf_no = masraf_no_;
   
   Line_Exists_ NUMBER;
BEGIN
   OPEN Line_Exists;
   FETCH Line_Exists INTO Line_Exists_;
   CLOSE Line_Exists;
   IF Line_Exists_ >0 THEN
      error_sys.system_general('Satirlari olan bir masraf silinemez');
   END IF;
   key_ := masraf_no_||'^';   
         
   IF harkt_masraf_giris_api.Get_Durum_Db(masraf_no_) != 'TASLAK' THEN
     error_sys.system_general('Durum Taslak degilken kaydi silemezsiniz!');
   END IF; 
      
   Reference_SYS.Check_Restricted_Delete('HarktMasrafGiris', key_);
  
   delete from harkt_masraf_giris_tab where masraf_no = masraf_no_;
END masraf_sil_odoo2_ifs;

PROCEDURE masraf_satir_sil_odoo2_ifs(masraf_no_ varchar2, satir_no_ number)
IS
  key_ varchar2(2000);
BEGIN
  key_ := masraf_no_||'^'||satir_no_||'^';
  IF harkt_masraf_giris_api.get_durum_db(masraf_no_) != 'TASLAK' THEN
     error_sys.system_general('Durum Taslak degilken kaydi silemezsiniz!');
  END IF;   
      
  Reference_SYS.Check_Restricted_Delete('HarktMasrafGirisLine', masraf_no_||'^');
  
  delete from harkt_masraf_giris_line_tab where masraf_no = masraf_no_ and satir_no=satir_no_;
END masraf_satir_sil_odoo2_ifs;



PROCEDURE para_sil_odoo2_ifs(talep_id_ varchar2)
IS
   key_ VARCHAR2(2000);
   CURSOR Line_Exists IS
   SELECT COUNT(*)
    FROM HARKT_PARA_TALEP_LINE l
   WHERE l.talep_id = talep_id_;
   
   Line_Exists_ NUMBER;   
       
   CURSOR Masraf_Exists IS
   SELECT DISTINCT 1 
     FROM harkt_masraf_giris_line a, harkt_para_talep b
     where a.ilgili_talep_no = b.talep_id
     and b.talep_id = talep_id_;
     
   Masraf_Exists_ NUMBER;  
BEGIN
   OPEN Masraf_Exists;
   FETCH Masraf_Exists INTO Masraf_Exists_;
   CLOSE Masraf_Exists;   
      
   IF Masraf_Exists_ = 1 THEN
      error_sys.system_general('Masrafa bagli olan bir talep silinemez! Once bagli masrafi siliniz!');
   END IF;   
      
      
   OPEN Line_Exists;
   FETCH Line_Exists INTO Line_Exists_;
   CLOSE Line_Exists;   
      
   IF Line_Exists_ >0 THEN
      error_sys.system_general('Satirlari olan bir talep silinemez');
   END IF;   
   key_ := talep_id_||'^';
      
   --IF Get_Durum_Db(remrec_.talep_id) != 'TASLAK' THEN
   IF Harkt_para_talep_api.Get_Durum_Db(talep_id_) = 'ODENECEK' OR Harkt_para_talep_api.Get_Durum_Db(talep_id_) = 'ODENDI' THEN   
     error_sys.system_general('Durumu odenmis veya odenecek olan kaydi silemezsiniz!');
   END IF;  
       
   Reference_SYS.Check_Restricted_Delete('HarktParaTalep', key_);
  
   delete from harkt_para_talep_tab where talep_id = talep_id_;
END para_sil_odoo2_ifs;

PROCEDURE para_satir_sil_odoo2_ifs(talep_id_ varchar2, line_no_ number)
IS
  key_ varchar2(2000);
BEGIN
  key_ := talep_id_||'^'||line_no_||'^';
  IF harkt_para_talep_api.Get_Durum_Db(talep_id_) != 'TASLAK' THEN
     error_sys.system_general('Durum Taslak degilken kaydi silemezsiniz!');
  END IF;   
      
  Reference_SYS.Check_Restricted_Delete('HarktParaTalepLine', key_);
  
  delete from harkt_para_talep_line_tab where talep_id = talep_id_ and line_no=line_no_;
END para_satir_sil_odoo2_ifs;

procedure para_sil_ifs2_odoo(talep_id_ varchar2)
IS
  http_req      utl_http.req;
  http_resp     utl_http.resp;
  json_request_  VARCHAR2(32767);
  req_ varchar2(32767) := '';
  v_len NUMBER;
  json_response varchar2(32767);
  v_txt varchar2(32767);
  date_approved_line_ varchar2(4000);
  histories_ varchar2(4000);
BEGIN
  FOR rec_ IN(select o.*
     from odoo_portal_param_tab o where param_name='ODOO_SERVER') LOOP
       req_ := '
        {
          "talep_no": "'||talep_id_||'",
          "supercall": 1
        }';
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","harkt.para.talep","remove_func",['||req_||']]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
   end loop;
   dbms_output.put_line('3');
   UTL_HTTP.SET_BODY_CHARSET('UTF-8');
   UTL_HTTP.set_header(http_req, 'Connection', 'close');
   UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
   UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
   UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
    dbms_output.put_line('4');
    http_resp := UTL_HTTP.get_response(http_req);
     dbms_output.put_line('5');
   utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
   json_response := null;
   dbms_output.put_line('Ýstek');
    dbms_output.put_line(json_request_);
   FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
   LOOP
       utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
       json_response := json_response || v_txt; -- build up CLOB
   END LOOP;
   utl_http.end_response(http_resp);
   dbms_output.put_line('Dönüþ');
   dbms_output.put_line(json_response);
   if not json_response like '%"result": true%' then
      error_sys.system_general(talep_id_||':'||substr(json_response,1,1900));
   end if;
END para_sil_ifs2_odoo;

procedure para_satir_sil_ifs2_odoo(talep_id_ varchar2, satir_no_ number)
IS
  http_req      utl_http.req;
  http_resp     utl_http.resp;
  json_request_  VARCHAR2(32767);
  req_ varchar2(32767) := '';
  v_len NUMBER;
  json_response varchar2(32767);
  v_txt varchar2(32767);
  date_approved_line_ varchar2(4000);
  histories_ varchar2(4000);
BEGIN
  FOR rec_ IN(select o.*
     from odoo_portal_param_tab o where param_name='ODOO_SERVER') LOOP
       req_ := '
        {
          "talep_no": "'||talep_id_||'",
          "satir_no": '||satir_no_||',
          "supercall": 1
        }';
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","harkt.para.talep.line","remove_func",['||req_||']]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
   end loop;
   dbms_output.put_line('3');
   UTL_HTTP.SET_BODY_CHARSET('UTF-8');
   UTL_HTTP.set_header(http_req, 'Connection', 'close');
   UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
   UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
   UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
    dbms_output.put_line('4');
    http_resp := UTL_HTTP.get_response(http_req);
     dbms_output.put_line('5');
   utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
   json_response := null;
   dbms_output.put_line('Ýstek');
    dbms_output.put_line(json_request_);
   FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
   LOOP
       utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
       json_response := json_response || v_txt; -- build up CLOB
   END LOOP;
   utl_http.end_response(http_resp);
   dbms_output.put_line('Dönüþ');
   dbms_output.put_line(json_response);
   if not json_response like '%"result": true%' then
      error_sys.system_general(talep_id_||':'||substr(json_response,1,1900));
   end if;
END para_satir_sil_ifs2_odoo;


procedure masraf_sil_ifs2_odoo(masraf_no_ varchar2)
IS
  http_req      utl_http.req;
  http_resp     utl_http.resp;
  json_request_  VARCHAR2(32767);
  req_ varchar2(32767) := '';
  v_len NUMBER;
  json_response varchar2(32767);
  v_txt varchar2(32767);
  date_approved_line_ varchar2(4000);
  histories_ varchar2(4000);
BEGIN
  FOR rec_ IN(select o.*
     from odoo_portal_param_tab o where param_name='ODOO_SERVER') LOOP
       req_ := '
        {
          "masraf_no": "'||masraf_no_||'",
          "supercall": 1
        }';
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","harkt.masraf","remove_func",['||req_||']]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
   end loop;
   dbms_output.put_line('3');
   UTL_HTTP.SET_BODY_CHARSET('UTF-8');
   UTL_HTTP.set_header(http_req, 'Connection', 'close');
   UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
   UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
   UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
    dbms_output.put_line('4');
    http_resp := UTL_HTTP.get_response(http_req);
     dbms_output.put_line('5');
   utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
   json_response := null;
   dbms_output.put_line('Ýstek');
    dbms_output.put_line(json_request_);
   FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
   LOOP
       utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
       json_response := json_response || v_txt; -- build up CLOB
   END LOOP;
   utl_http.end_response(http_resp);
   dbms_output.put_line('Dönüþ');
   dbms_output.put_line(json_response);
   if not json_response like '%"result": true%' then
      error_sys.system_general(masraf_no_||':'||substr(json_response,1,1900));
   end if;
END masraf_sil_ifs2_odoo;



procedure masraf_satir_sil_ifs2_odoo(masraf_no_ varchar2, satir_no_ number)
IS
  http_req      utl_http.req;
  http_resp     utl_http.resp;
  json_request_  VARCHAR2(32767);
  req_ varchar2(32767) := '';
  v_len NUMBER;
  json_response varchar2(32767);
  v_txt varchar2(32767);
  date_approved_line_ varchar2(4000);
  histories_ varchar2(4000);
BEGIN
  FOR rec_ IN(select o.*
     from odoo_portal_param_tab o where param_name='ODOO_SERVER') LOOP
       req_ := '
        {
          "masraf_no": "'||masraf_no_||'",
          "satir_no": '||satir_no_||',
          "supercall": 1
        }';
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","harkt.masraf.line","remove_func",['||req_||']]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
   end loop;
   dbms_output.put_line('3');
   UTL_HTTP.SET_BODY_CHARSET('UTF-8');
   UTL_HTTP.set_header(http_req, 'Connection', 'close');
   UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
   UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
   UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
    dbms_output.put_line('4');
    http_resp := UTL_HTTP.get_response(http_req);
     dbms_output.put_line('5');
   utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
   json_response := null;
   dbms_output.put_line('Ýstek');
    dbms_output.put_line(json_request_);
   FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
   LOOP
       utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
       json_response := json_response || v_txt; -- build up CLOB
   END LOOP;
   utl_http.end_response(http_resp);
   dbms_output.put_line('Dönüþ');
   dbms_output.put_line(json_response);
   if not json_response like '%"result": true%' then
      error_sys.system_general(masraf_no_||':'||substr(json_response,1,1900));
   end if;
END masraf_satir_sil_ifs2_odoo;

procedure para_ifs2_odoo(talep_id_ varchar2)
IS
  http_req      utl_http.req;
  http_resp     utl_http.resp;
  json_request_  VARCHAR2(32767);
  req_ varchar2(32767) := '';
  v_len NUMBER;
  json_response varchar2(32767);
  v_txt varchar2(32767);
  date_approved_line_ varchar2(4000);
  histories_ varchar2(4000);
BEGIN
  FOR rec_ IN(select o.*,talep_id, company, talep_tarihi, decode(nvl(proje_turu,'*'),'ETUT','Etut','TALIMAT','Talimat',proje_turu) proje_turu, proje_id, bolum, talep_eden, durum, ref_talep_no, note_text, para_birimi, onay_aciklamasi, currency_code, kiralik, kiralik_plaka
     from odoo_portal_param_tab o, harkt_para_talep_tab a where param_name='ODOO_SERVER' and talep_id = talep_id_) LOOP
       FOR hrec_ IN(select a.*
         from approval_routing_tab a where  a.lu_name = 'HarktParaTalep'
              and a.key_ref = 'TALEP_ID='||talep_id_||'^') LOOP
              
             if hrec_.app_date is not null then
                date_approved_line_ := '"sign_date":"'||to_char(hrec_.app_date,'yyyy-MM-dd hh24:mi:ss')||'",';
             else
                date_approved_line_ := '';
             END IF;
             histories_ := histories_ ||'{
               "para_talep_id": 0, 
               "sequence_no": '||hrec_.line_no||', 
               "route": '||hrec_.step_no||', 
               "approver_sign":"'||hrec_.app_sign||'",'||
               date_approved_line_||'
               "approval_status":"'||hrec_.approval_status||'",
               "emp_no":"'||hrec_.person_id||'",
               "reject_reason":"'||hrec_.note||'"
             },';
       END LOOP;
       if histories_ like '%,' then
         histories_ := substr(histories_,1,length(histories_)-1);
       end if;
       req_ := '
        {
          "company": "'|| rec_.company||'",
          "talep_no": "'|| rec_.talep_id||'",
          "kisi_id": "'|| substr(rec_.talep_eden,1,5)||'",
          "bolum": "'|| rec_.bolum||'",
          "notlar": "'|| replace(replace(replace(replace(replace(rec_.note_text,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'",
          "currency_code": "'|| rec_.currency_code||'",
          "talep_tarihi": "'|| to_char(nvl(rec_.talep_tarihi,to_date('01.01.1900','dd.MM.yyyy')),'yyyy-MM-dd hh24:mi:ss') ||'",
          "proje": "'|| rec_.proje_id||'",
          "proje_turu": "'|| rec_.proje_turu||'",
          "ref_talep": "'|| rec_.ref_talep_no||'",
          "durum": "'|| rec_.durum||'",
          "histories":['||histories_||']
        }';
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","harkt.para.talep","write_or_create",['||req_||']]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
   end loop;
   dbms_output.put_line('3');
   UTL_HTTP.SET_BODY_CHARSET('UTF-8');
   UTL_HTTP.set_header(http_req, 'Connection', 'close');
   UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
   UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
   UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
    dbms_output.put_line('4');
    http_resp := UTL_HTTP.get_response(http_req);
     dbms_output.put_line('5');
   utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
   json_response := null;
   dbms_output.put_line('Ýstek');
    dbms_output.put_line(json_request_);
   FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
   LOOP
       utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
       json_response := json_response || v_txt; -- build up CLOB
   END LOOP;
   utl_http.end_response(http_resp);
   dbms_output.put_line('Dönüþ');
   dbms_output.put_line(json_response);
   if not json_response like '%"result": true%' then
      error_sys.system_general(talep_id_||':'||substr(json_response,1,1900));
   end if;
END para_ifs2_odoo;


procedure para_satir_ifs2_odoo(talep_id_ varchar2, satir_no_ number)
IS
http_req      utl_http.req;
  http_resp     utl_http.resp;
  json_request_  VARCHAR2(32767);
  req_ varchar2(32767) := '';
  v_len NUMBER;
  json_response varchar2(32767);
  v_txt varchar2(32767);
BEGIN
  
  FOR rec_ IN(select o.*,
    talep_id, line_no, person_id, company, project_id, currency, talep_on_grup, talep_turu, miktar, tutar, line_desc, country, varlik_kodu, contract, bolge, harici, hrc_adi_soyadi, hrc_kimlik_no, hrc_adres, hrc_phone, hrc_iban, departman, kiralik, kiralik_plaka,
    a.currency_rate
    
     from odoo_portal_param_tab o, harkt_para_talep_line_tab a where param_name='ODOO_SERVER' and talep_id = talep_id_ and line_no=satir_no_) LOOP
      req_ := '
        {
          "para_talep_no": "'|| rec_.talep_id||'",
          "satir_no": "'||rec_.line_no||'",
          "talep_edilen_id": "'|| substr(rec_.person_id,2,5)||'",
          "company_id": "'|| rec_.company ||'",
          "ongrup_no": "'|| rec_.talep_on_grup||'",
          "masraf_turu": "'|| rec_.talep_turu||'",
          "miktar": "'|| replace(rec_.miktar,',','.')||'",
          "tutar": "'|| replace(rec_.tutar,',','.')||'",
          "aciklama": "'|| replace(replace(replace(replace(replace(rec_.line_desc,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'",
          "country": "'|| rec_.country||'",
          "varlik": "'|| rec_.varlik_kodu||'",
          "bolge": "'|| rec_.bolge||'",
          "harici": "'|| rec_.harici||'",
          "doviz_kuru": "'||rec_.currency_rate||'",
          "harici_ad_soyad": "'|| replace(replace(replace(replace(replace(rec_.hrc_adi_soyadi,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'",
          "harici_kimlik_no": "'|| replace(replace(replace(replace(replace(rec_.hrc_kimlik_no,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'",
          "harici_adres": "'|| replace(replace(replace(replace(replace(rec_.hrc_adres,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'",
          "harici_telefon": "'|| replace(replace(replace(replace(replace(rec_.hrc_phone,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'",
          "harici_iban": "'|| replace(replace(replace(replace(replace(rec_.hrc_iban,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'",
          "kiralik": "'|| rec_.kiralik||'",
          "kiralik_plaka": "'|| replace(replace(replace(replace(replace(rec_.kiralik_plaka,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'"
        }';
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","harkt.para.talep.line","write_or_create",['||req_||']]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
   end loop;
   dbms_output.put_line('3');
   UTL_HTTP.SET_BODY_CHARSET('UTF-8');
   UTL_HTTP.set_header(http_req, 'Connection', 'close');
   UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
   UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
   UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
   dbms_output.put_line('4');
   http_resp := UTL_HTTP.get_response(http_req);
   dbms_output.put_line('5');
   utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
   json_response := null;
   dbms_output.put_line('Ýstek');
   dbms_output.put_line(json_request_);
   FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
   LOOP
       utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
       json_response := json_response || v_txt; -- build up CLOB
   END LOOP;
   utl_http.end_response(http_resp);
   dbms_output.put_line('Dönüþ');
   dbms_output.put_line(json_response);
   if not json_response like '%"result": true%' then
      error_sys.system_general(talep_id_||'-'||satir_no_||'-'||substr(json_response,1,1900));
   end if;
END para_satir_ifs2_odoo;

PROCEDURE para_talebi_odoo2_ifs(
  company_id_         IN     VARCHAR2,
  talep_eden_id_      IN     VARCHAR2,
  talep_tarihi_       IN     DATE,
  bolum_              IN     VARCHAR2,
  notlar_             IN     VARCHAR2,
  currency_           IN     VARCHAR2,
  proje_              IN     VARCHAR2,
  proje_turu_         IN     VARCHAR2,
  durum_              IN     VARCHAR2,
  ref_talep_          IN     VARCHAR2,
  details_            IN     CLOB,
  para_talep_no_      IN OUT VARCHAR2)
IS
  dec_sep_ varchar2(1);
  tho_sep_ varchar2(1);
  test_ number;
  info_ varchar2(32000);
  objid_ varchar2(32000);
  objversion_ varchar2(32000);
  attr_ varchar2(32000);
  attr_cf_ varchar2(32000);
  cnt_ number;
BEGIN
  --ERROR_SYS.SYSTEM_GENERAL('ÇALIÞMA YAPILIYOR'||TALEP_EDEN_ID_);
  begin
     test_:= round(to_NUMBER('100.02'),2);
     dec_sep_:='.';
     tho_sep_:=',';
  exception when others then
     dec_sep_:=',';
     tho_sep_:='.';    
  end;
  info_ := null;
  objid_ := null;
  objversion_ := null;
  attr_ := null;
  Client_sys.Add_To_Attr('COMPANY', company_id_, attr_ );
  Client_sys.Add_To_Attr('TALEP_EDEN', talep_eden_id_, attr_ );
  Client_sys.Add_To_Attr('BOLUM', bolum_, attr_ );
  Client_sys.Add_To_Attr('NOTE_TEXT', notlar_, attr_ );
  Client_sys.Add_To_Attr('CURRENCY_CODE', currency_, attr_ );
  Client_sys.Add_To_Attr('TALEP_TARIHI', talep_tarihi_, attr_ );
  Client_sys.Add_To_Attr('PROJE_ID', proje_, attr_ );
  Client_sys.Add_To_Attr('PROJE_TURU', proje_turu_, attr_ );
  Client_sys.Add_To_Attr('REF_TALEP', ref_talep_, attr_ );
  Client_sys.Add_To_Attr('ODOO', 'Y', attr_ );
  IF para_talep_no_ IS NOT NULL THEN
    IF durum_ IS NULL OR durum_ = 'TASLAK' THEN
      for talep_ in(select * from harkt_para_talep where talep_id= para_talep_no_ and durum_db='TASLAK') LOOP
        info_ := null;
        objid_ := talep_.objid;
        objversion_ := talep_.objversion;
        Harkt_para_talep_api.Modify__(info_, objid_, objversion_, attr_, 'DO');
      END LOOP;
    ELSIF durum_ = 'YAYINLANDI' THEN
      harkt_para_talep_api.Set_Yayinlandi(para_talep_no_);
    ELSIF durum_ = 'YAYINLANDI' THEN
      harkt_para_talep_api.Set_Kontrol_Gonder(para_talep_no_);
    ELSIF durum_ = 'IPTAL' THEN
      odoo_portal_api.para_talebi_set_iptal(para_talep_no_);
    END IF;
  ELSE
    Client_sys.Add_To_Attr('DURUM_DB', 'TASLAK', attr_ );
    Harkt_para_talep_api.New__(info_, objid_, objversion_, attr_, 'DO');
    para_talep_no_ := Client_sys.Get_Item_Value('TALEP_ID',attr_);
  END IF;
  IF durum_ IS NULL THEN
    for rec_ IN(
      select  satir_no, ongrup_no,masraf_turu,company_id,project_id,bolge_id,harici,talep_edilen_id,
      varlik_id,miktar,tutar,ulke,kiralik,kiralik_plaka,aciklama,harici_kimlik_no,
      harici_adres, harici_telefon,harici_iban,harici_ad_soyad,is_takip_no,bolum,
      doviz_kuru
      from xmltable('/ParaTalebi/ParaTalebiSatirlar/ParaTalebiSatir'
                        passINg XMLType(details_)
                       columns  SATIR_NO         NUMBER              path 'SATIR_NO',
                                ONGRUP_NO        VARCHAR2(200)       path 'ONGRUP_NO',
                                MASRAF_TURU      VARCHAR2(2000)      path 'MASRAF_TURU',
                                COMPANY_ID       VARCHAR2(200)       Path 'COMPANY_ID',
                                PROJECT_ID       VARCHAR2(200)       Path 'PROJECT_ID',
                                BOLGE_ID         VARCHAR2(200)       Path 'BOLGE_ID',
                                HARICI           VARCHAR2(200)       Path 'HARICI',
                                TALEP_EDILEN_ID  VARCHAR2(200)       Path 'TALEP_EDILEN_ID',
                                VARLIK_ID        VARCHAR2(200)       Path 'VARLIK_ID',
                                MIKTAR           VARCHAR2(200)       Path 'MIKTAR',
                                TUTAR            VARCHAR2(200)       Path 'TUTAR',
                                DOVIZ_KURU       VARCHAR2(200)       Path 'DOVIZ_KURU',
                                ULKE             VARCHAR2(200)       Path 'ULKE',
                                KIRALIK          VARCHAR2(200)       Path 'KIRALIK',
                                KIRALIK_PLAKA    VARCHAR2(200)       Path 'KIRALIK_PLAKA',
                                ACIKLAMA         VARCHAR2(4000)      Path 'ACIKLAMA',
                                HARICI_KIMLIK_NO VARCHAR2(200)       Path 'HARICI_KIMLIK_NO',
                                HARICI_ADRES     VARCHAR2(200)       Path 'HARICI_ADRES',
                                HARICI_TELEFON   VARCHAR2(200)       Path 'HARICI_TELEFON',
                                HARICI_IBAN      VARCHAR2(200)       Path 'HARICI_IBAN',
                                HARICI_AD_SOYAD  VARCHAR2(200)       Path 'HARICI_AD_SOYAD',
                                IS_TAKIP_NO      VARCHAR2(200)       Path 'IS_TAKIP_NO',
                                BOLUM            VARCHAR2(200)       Path 'BOLUM'
                        ) q
    ) LOOP
      info_ := null;
      objid_ := null;
      objversion_ := null;
      attr_ := null;
      
      Client_sys.Add_To_Attr('PERSON_ID', rec_.talep_edilen_id, attr_ );
      Client_sys.Add_To_Attr('COMPANY', rec_.company_id, attr_ );
      Client_sys.Add_To_Attr('PROJECT_ID', rec_.project_id, attr_ );
      Client_sys.Add_To_Attr('CURRENCY', currency_, attr_ );
      Client_sys.Add_To_Attr('CURRENCY_RATE', rec_.doviz_kuru, attr_ );
      Client_sys.Add_To_Attr('TALEP_ON_GRUP', rec_.ongrup_no, attr_ );
      Client_sys.Add_To_Attr('TALEP_TURU', rec_.masraf_turu, attr_ );
      Client_sys.Add_To_Attr('MIKTAR', rec_.miktar, attr_ );
      Client_sys.Add_To_Attr('TUTAR', rec_.tutar, attr_ );
      Client_sys.Add_To_Attr('LINE_DESC', rec_.aciklama, attr_ );
      Client_sys.Add_To_Attr('COUNTRY', rec_.ulke, attr_ );
      Client_sys.Add_To_Attr('VARLIK_KODU', rec_.varlik_id, attr_ );
      --Client_sys.Add_To_Attr('CONTRACT', ref_talep_, attr_ );
      Client_sys.Add_To_Attr('BOLGE', rec_.bolge_id, attr_ );
      Client_sys.Add_To_Attr('HARICI', rec_.harici, attr_ );
      Client_sys.Add_To_Attr('HRC_ADI_SOYADI', rec_.harici_ad_soyad, attr_ );
      Client_sys.Add_To_Attr('HRC_KIMLIK_NO', rec_.harici_kimlik_no, attr_ );
      Client_sys.Add_To_Attr('HRC_ADRES', rec_.harici_adres, attr_ );
      Client_sys.Add_To_Attr('HRC_PHONE', rec_.harici_telefon, attr_ );
      Client_sys.Add_To_Attr('HRC_IBAN', rec_.harici_iban, attr_ );
      --Client_sys.Add_To_Attr('DEPARTMAN', ref_talep_, attr_ );
      Client_sys.Add_To_Attr('KIRALIK', rec_.kiralik, attr_ );
      Client_sys.Add_To_Attr('KIRALIK_PLAKA', rec_.kiralik_plaka, attr_ );
      Client_sys.Add_To_Attr('DEPARTMAN', harkt_para_talep_api.Get_Bolum(para_talep_no_), attr_ );
      Client_sys.Add_To_Attr('ODOO', 'Y', attr_ );
      --Client_sys.Add_To_Attr('CURRENCY_RATE', ref_talep_, attr_ );
      select count(1) into cnt_ from harkt_para_talep_line l where l.talep_id= para_talep_no_ and l.line_no=rec_.satir_no;
        
      IF cnt_ > 0 THEN
        select count(1) into cnt_ from harkt_para_talep_line l,
        harkt_para_talep t where l.talep_id = t.talep_id and l.talep_id= para_talep_no_ and l.line_no=rec_.satir_no
        and t.durum_db = 'TASLAK';
        IF cnt_ > 0 THEN
          for talep_ in(select * from harkt_para_talep_line where talep_id= para_talep_no_ and line_no=rec_.satir_no) LOOP
            info_ := null;
            objid_ := talep_.objid;
            objversion_ := talep_.objversion;
            Harkt_para_talep_line_api.Modify__(info_, objid_, objversion_, attr_, 'DO');
          END LOOP;
        END IF;
      ELSE
        Client_sys.Add_To_Attr('TALEP_ID', para_talep_no_, attr_ );
        Client_sys.Add_To_Attr('LINE_NO', rec_.satir_no, attr_ );
        Harkt_para_talep_line_api.New__(info_, objid_, objversion_, attr_, 'DO');
      END IF;

      for rec2_ in(select * from harkt_para_talep_line where talep_id=para_talep_no_ and line_no=rec_.satir_no) 
      loop
        info_ := null;
        attr_ := null;
        objid_ := rec2_.objid;
          
        Client_sys.Add_To_Attr('CF$_IS_TAKIP_NO', rec_.is_takip_no, attr_cf_ );
        IFSAPP.HARKT_PARA_TALEP_LINE_CFP.Cf_Modify__(info_ , objid_ , attr_cf_ , attr_ , 'DO' );
      end loop;
      
      
    end loop;
    
    
    for rec_ IN(
      select * from harkt_para_talep_line tl where tl.talep_id = para_talep_no_ AND line_no not in
        (
      select  satir_no
      from xmltable('/ParaTalebi/ParaTalebiSatirlar/ParaTalebiSatir'
                        passINg XMLType(details_)
                       columns  SATIR_NO         NUMBER              path 'SATIR_NO'
                        ) q)) LOOP
      odoo_portal_api.para_satir_sil_odoo2_ifs(para_talep_no_,rec_.line_no);
    end loop;
  END IF;
END para_talebi_odoo2_ifs;

PROCEDURE para_talebi_onay_odoo2_ifs(
  talep_id_ VARCHAR2,
  line_no_ number,
  step_no_ number,
  approval_status_db_ varchar2 default 'APP',
  note_ varchar2 default null) 
IS
BEGIN
  FOR rec_ in(SELECT * FROM approval_routing_tab a
    WHERE lu_name='HarktParaTalep' 
    AND key_ref = 'TALEP_ID='||talep_id_||'^'
    AND a.line_no= line_no_
    AND a.step_no= step_no_) loop
    BEGIN
      update approval_routing_tab a set note = note_ where
      lu_name='HarktParaTalep' 
      AND key_ref = 'TALEP_ID='||talep_id_||'^'
      AND a.line_no= line_no_
      AND a.step_no= step_no_;
      IFSAPP.approval_routing_api.Set_Next_App_Step(
        'HarktParaTalep',
        'TALEP_ID='||talep_id_||'^',
        line_no_, 
        step_no_,
        approval_status_db_);
    END;
  END LOOP;
END para_talebi_onay_odoo2_ifs;

PROCEDURE masraf_odoo2_ifs(
  company_id_         IN     VARCHAR2,
  user_id_            IN     VARCHAR2,
  bolum_              IN     VARCHAR2,
  notlar_             IN     VARCHAR2,
  currency_           IN     VARCHAR2,
  durum_              IN     VARCHAR2,
  details_            IN     CLOB,
  masraf_no_          IN     OUT VARCHAR2)
IS
  dec_sep_ varchar2(1);
  tho_sep_ varchar2(1);
  test_ number;
  info_ varchar2(32000);
  objid_ varchar2(32000);
  objversion_ varchar2(32000);
  attr_ varchar2(32000);
  attr_cf_ varchar2(32000);
  cnt_ number;
BEGIN
  info_ := null;
  objid_ := null;
  objversion_ := null;
  attr_ := null;
  Client_sys.Add_To_Attr('COMPANY', company_id_, attr_ );
  Client_sys.Add_To_Attr('KISI_ID', user_id_, attr_ );
  Client_sys.Add_To_Attr('BOLUM', bolum_, attr_ );
  Client_sys.Add_To_Attr('NOTE_TEXT', notlar_, attr_ );
  Client_sys.Add_To_Attr('CURRENCY_CODE', currency_, attr_ );
  Client_sys.Add_To_Attr('ODOO', 'Y', attr_ );
  
  IF masraf_no_ IS NOT NULL THEN
    IF durum_ IS NULL or durum_ = 'TASLAK' THEN
      for masraf_ in(select * from harkt_masraf_giris where masraf_no= masraf_no_ and durum_db='TASLAK') LOOP
        info_ := null;
        objid_ := masraf_.objid;
        objversion_ := masraf_.objversion;
        Harkt_masraf_giris_api.Modify__(info_, objid_, objversion_, attr_, 'DO');
      END LOOP;
    ELSIF durum_ = 'YAYINLANDI' THEN
       odoo_portal_api.masraf_set_yayinlandi(masraf_no_);
    ELSIF durum_ = 'KONTROL_BEKLIYOR' THEN
       HARKT_MASRAF_GIRIS_API.Set_Kontrol_Gonder(masraf_no_);
    ELSIF durum_ = 'IPTAL' THEN
       odoo_portal_api.masraf_set_iptal(masraf_no_); 
    END IF;
  ELSE
    Client_sys.Add_To_Attr('DURUM_DB', 'TASLAK', attr_ );
    Harkt_masraf_giris_api.New__(info_, objid_, objversion_, attr_, 'DO');
    masraf_no_ := Client_sys.Get_Item_Value('MASRAF_NO',attr_);
  END IF;

  IF durum_ IS NULL OR durum_ = 'TASLAK' THEN
    for rec_ IN(
      select  satir_no, COMPANY_ID,BOLGE_ID,PARA_TALEP_ID,FIS_TARIHI,KISI_ID,BOLUM_ID,PROJECT_ID,
      ACTIVITY_ID,IADE_HESAP_ID,PERSONEL_VIRMANI,VIRMAN_CALISAN_ID,MAAS_KESINTISI,HARICI_ARAC_PLAKA,ONGRUP_ID,MASRAF_TURU_ID,
      GIDER_YERI_ID, MIKTAR,CURRENCY_ID,TUTAR,TUTAR_TRY,TUTAR_KDV_HARIC,TUTAR_TRY_KDV_HARIC,
      TEDARIKCI_BELGE_NO,KDV_ORANI,KIRALIK,FIRMA_ARACI_PLAKA_ID,EV_KODU_ID,IS_EMRI_NO,
      ODENDI,ODENMEDI,ACIKLAMA,PARA_TALEBI_OLUSTUR,PARA_TALEBI_VAR,BELGELI,BELGESIZ,BELGE_SONRADAN,AVANS_IADESI
      from xmltable('/Masraf/MasrafSatirlar/MasrafSatir'
                        passINg XMLType(details_)
                       columns  SATIR_NO             NUMBER              path 'SATIR_NO',
                                COMPANY_ID           VARCHAR2(200)       path 'COMPANY_ID',
                                BOLGE_ID             VARCHAR2(2000)      path 'BOLGE_ID',
                                PARA_TALEP_ID        VARCHAR2(200)       Path 'PARA_TALEP_ID',
                                FIS_TARIHI           VARCHAR2(200)       Path 'FIS_TARIHI',
                                KISI_ID              VARCHAR2(200)       Path 'KISI_ID',
                                BOLUM_ID             VARCHAR2(200)       Path 'BOLUM_ID',
                                PROJECT_ID           VARCHAR2(200)       Path 'PROJECT_ID',
                                ACTIVITY_ID          VARCHAR2(200)       Path 'ACTIVITY_ID',
                                IADE_HESAP_ID        VARCHAR2(200)       Path 'IADE_HESAP_ID',
                                PERSONEL_VIRMANI     VARCHAR2(200)       Path 'PERSONEL_VIRMANI',
                                VIRMAN_CALISAN_ID    VARCHAR2(200)       Path 'VIRMAN_CALISAN_ID',
                                MAAS_KESINTISI       VARCHAR2(200)       Path 'MAAS_KESINTISI',
                                HARICI_ARAC_PLAKA    VARCHAR2(200)       Path 'HARICI_ARAC_PLAKA',
                                ONGRUP_ID            VARCHAR2(4000)      Path 'ONGRUP_ID',
                                MASRAF_TURU_ID       VARCHAR2(200)       Path 'MASRAF_TURU_ID',
                                GIDER_YERI_ID        VARCHAR2(200)       Path 'GIDER_YERI_ID',
                                MIKTAR               VARCHAR2(200)       Path 'MIKTAR',
                                CURRENCY_ID          VARCHAR2(200)       Path 'CURRENCY_ID',
                                TUTAR                VARCHAR2(200)       Path 'TUTAR',
                                TUTAR_TRY            VARCHAR2(200)       Path 'TUTAR_TRY',
                                TUTAR_KDV_HARIC      VARCHAR2(200)       Path 'TUTAR_KDV_HARIC',
                                TUTAR_TRY_KDV_HARIC  VARCHAR2(200)       Path 'TUTAR_TRY_KDV_HARIC',
                                TEDARIKCI_BELGE_NO   VARCHAR2(200)       Path 'TEDARIKCI_BELGE_NO',
                                KDV_ORANI            VARCHAR2(200)       Path 'KDV_ORANI',
                                KIRALIK              VARCHAR2(200)       Path 'KIRALIK',
                                FIRMA_ARACI_PLAKA_ID VARCHAR2(200)       Path 'FIRMA_ARACI_PLAKA_ID',
                                EV_KODU_ID           VARCHAR2(200)       Path 'EV_KODU_ID',
                                IS_EMRI_NO           VARCHAR2(200)       Path 'IS_EMRI_NO',
                                ODENDI               VARCHAR2(200)       Path 'ODENDI',
                                ODENMEDI             VARCHAR2(200)       Path 'ODENMEDI',
                                ACIKLAMA             VARCHAR2(200)       Path 'ACIKLAMA',
                                PARA_TALEBI_OLUSTUR  VARCHAR2(200)       Path 'PARA_TALEBI_OLUSTUR',
                                PARA_TALEBI_VAR      VARCHAR2(200)       Path 'PARA_TALEBI_VAR',
                                BELGELI              VARCHAR2(200)       Path 'BELGELI',
                                BELGESIZ             VARCHAR2(200)       Path 'BELGESIZ',
                                BELGE_SONRADAN       VARCHAR2(200)       Path 'BELGE_SONRADAN',
                                AVANS_IADESI         VARCHAR2(200)       Path 'AVANS_IADESI'
                        ) q
    ) LOOP
      info_ := null;
      objid_ := null;
      objversion_ := null;
      attr_ := null;
      
      Client_sys.Add_To_Attr('BOLGE', rec_.bolge_id, attr_ );
      Client_sys.Add_To_Attr('COMPANY', rec_.company_id, attr_ );
      Client_sys.Add_To_Attr('ILGILI_TALEP_NO', rec_.para_talep_id, attr_ );
      Client_sys.Add_To_Attr('MASRAF_GIRIS_TRH', rec_.fis_tarihi, attr_ );
      Client_sys.Add_To_Attr('KISI_ID', rec_.kisi_id, attr_ );
      
      Client_sys.Add_To_Attr('BOLUM', rec_.bolum_id, attr_ );
      Client_sys.Add_To_Attr('PROJECT_ID', rec_.PROJECT_ID, attr_ );
      Client_sys.Add_To_Attr('ACTIVITY_SEQ', rec_.ACTIVITY_ID, attr_ );
      Client_sys.Add_To_Attr('IADE_HESAP_KODU', rec_.IADE_HESAP_ID, attr_ );
      Client_sys.Add_To_Attr('PERSONEL_VIRMANI', rec_.PERSONEL_VIRMANI, attr_ );
      Client_sys.Add_To_Attr('VIRMAN_YAPILACAK_KISI', rec_.VIRMAN_CALISAN_ID, attr_ );
      Client_sys.Add_To_Attr('MAAS_KESINTISI', rec_.MAAS_KESINTISI, attr_ );
      --Client_sys.Add_To_Attr('CONTRACT', ref_talep_, attr_ );
      Client_sys.Add_To_Attr('KIRALIK_PLAKA', rec_.HARICI_ARAC_PLAKA, attr_ );
      Client_sys.Add_To_Attr('MASRAF_ON_GRUP', rec_.ONGRUP_ID, attr_ );
      Client_sys.Add_To_Attr('MASRAF_TIPI', rec_.MASRAF_TURU_ID, attr_ );
      Client_sys.Add_To_Attr('GIDER_YERI', rec_.GIDER_YERI_ID, attr_ );
      Client_sys.Add_To_Attr('MIKTAR', rec_.MIKTAR, attr_ );
      Client_sys.Add_To_Attr('CURRENCY', rec_.CURRENCY_ID, attr_ );
      Client_sys.Add_To_Attr('TRY_TOPLAM_TUTAR', rec_.TUTAR_TRY, attr_ );
      Client_sys.Add_To_Attr('TOPLAM_TUTAR', rec_.TUTAR, attr_ );
      Client_sys.Add_To_Attr('KDV_ORANI', rec_.KDV_ORANI, attr_ );
      Client_sys.Add_To_Attr('TEDARIKCI', rec_.TEDARIKCI_BELGE_NO, attr_ );
      Client_sys.Add_To_Attr('KIRALIK', rec_.KIRALIK, attr_ );
      Client_sys.Add_To_Attr('PLAKA', rec_.FIRMA_ARACI_PLAKA_ID, attr_ );
      Client_sys.Add_To_Attr('EV_KODU', rec_.EV_KODU_ID, attr_ );
      Client_sys.Add_To_Attr('IS_EMRI_NO', rec_.IS_EMRI_NO, attr_ );
      Client_sys.Add_To_Attr('ODEME_DURUM', rec_.ODENDI, attr_ );
      Client_sys.Add_To_Attr('ODENMEDI', rec_.ODENMEDI, attr_ );
      Client_sys.Add_To_Attr('NOTE_TEXT', rec_.ACIKLAMA, attr_ );
      Client_sys.Add_To_Attr('TALEP_YOK', rec_.PARA_TALEBI_OLUSTUR, attr_ );
      Client_sys.Add_To_Attr('TALEP_VAR', rec_.PARA_TALEBI_VAR, attr_ );
      Client_sys.Add_To_Attr('BELGELI', rec_.BELGELI, attr_ );
      Client_sys.Add_To_Attr('BELGE_DURUM', rec_.BELGESIZ, attr_ );
      Client_sys.Add_To_Attr('BELGE_GELECEK', rec_.BELGE_SONRADAN, attr_ );
      Client_sys.Add_To_Attr('AVANS_IADESI', rec_.AVANS_IADESI, attr_ );
      Client_sys.Add_To_Attr('ODOO', 'Y', attr_ );
      --Client_sys.Add_To_Attr('CURRENCY_RATE', ref_talep_, attr_ );
      select count(1) into cnt_ from harkt_masraf_giris_line_tab where masraf_no = masraf_no_ and satir_no=rec_.satir_no;
      
      
      IF cnt_ > 0 THEN
        select count(1) into cnt_ from harkt_masraf_giris_line_tab l,
        harkt_masraf_giris_tab t where l.masraf_no = t.masraf_no and l.masraf_no= masraf_no_ and l.satir_no=rec_.satir_no
        and t.durum = 'TASLAK';
        IF cnt_>0 THEN
          for masraf_ in(select * from harkt_masraf_giris_line where masraf_no = masraf_no_ and satir_no=rec_.satir_no) LOOP
            info_ := null;
            objid_ := masraf_.objid;
            objversion_ := masraf_.objversion;
            Harkt_masraf_giris_line_api.Modify__(info_, objid_, objversion_, attr_, 'DO');
          END LOOP;
        END IF;
      ELSE
        Client_sys.Add_To_Attr('MASRAF_NO', masraf_no_, attr_ );
        Client_sys.Add_To_Attr('SATIR_NO', rec_.satir_no, attr_ );
        Harkt_masraf_giris_line_api.New__(info_, objid_, objversion_, attr_, 'DO');
      END IF;
    end loop;
    
    for rec_ IN(
      select * from harkt_masraf_giris_line tl where tl.masraf_no = masraf_no_ AND satir_no not in
        (
      select  satir_no
      from xmltable('/Masraf/MasrafSatirlar/MasrafSatir'
                        passINg XMLType(details_)
                       columns  SATIR_NO         NUMBER              path 'SATIR_NO'
                        ) q)) LOOP
      odoo_portal_api.masraf_satir_sil_odoo2_ifs(masraf_no_,rec_.satir_no);
    end loop;
  END IF;
  
END masraf_odoo2_ifs;

procedure masraf_ifs2_odoo(masraf_no_ varchar2)
IS
  http_req      utl_http.req;
  http_resp     utl_http.resp;
  json_request_  VARCHAR2(32767);
  req_ varchar2(32767) := '';
  v_len NUMBER;
  json_response varchar2(32767);
  v_txt varchar2(32767);
  date_approved_line_ varchar2(4000);
  histories_ varchar2(4000);
BEGIN
  FOR rec_ IN(select o.*,masraf_no, company, kisi_id, bolum, durum, note_text, currency_code
     from odoo_portal_param_tab o, harkt_masraf_giris_tab a where param_name='ODOO_SERVER' and masraf_no = masraf_no_) LOOP
       
       req_ := '
        {
          "company": "'|| rec_.company||'",
          "masraf_no": "'|| rec_.masraf_no||'",
          "kisi_id": "'|| substr(rec_.kisi_id,2,5)||'",
          "bolum": "'|| rec_.bolum||'",
          "notlar": "'|| replace(replace(replace(replace(replace(rec_.note_text,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'",
          "currency_code": "'|| rec_.currency_code||'",
          "durum": "'|| rec_.durum||'"
        }';
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","harkt.masraf","write_or_create",['||req_||']]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
   end loop;
   dbms_output.put_line('3');
   UTL_HTTP.SET_BODY_CHARSET('UTF-8');
   UTL_HTTP.set_header(http_req, 'Connection', 'close');
   UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
   UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
   UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
    dbms_output.put_line('4');
    http_resp := UTL_HTTP.get_response(http_req);
     dbms_output.put_line('5');
   utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
   json_response := null;
   dbms_output.put_line('Ýstek');
    dbms_output.put_line(json_request_);
   FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
   LOOP
       utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
       json_response := json_response || v_txt; -- build up CLOB
   END LOOP;
   utl_http.end_response(http_resp);
   dbms_output.put_line('Dönüþ');
   dbms_output.put_line(json_response);
   if not json_response like '%"result": true%' then
      error_sys.system_general(masraf_no_||':'||substr(json_response,1,1900));
   end if;
END masraf_ifs2_odoo;



procedure masraf_satir_ifs2_odoo(masraf_no_ varchar2, line_no_ number)
IS
http_req      utl_http.req;
  http_resp     utl_http.resp;
  json_request_  VARCHAR2(32767);
  req_ varchar2(32767) := '';
  v_len NUMBER;
  json_response varchar2(32767);
  v_txt varchar2(32767);
BEGIN
  
  FOR rec_ IN(select o.*,
    masraf_no, satir_no, kisi_id, company,
    contract, bolge, bolum, durum, note_text,
    project_id, masraf_giris_trh, masraf_on_grup, 
    masraf_tipi, gider_yeri, tutar, kdv_orani, miktar, 
    currency, tedarikci, belge_durum, odeme_durum, plaka, 
    kiralik, ev_kodu, is_emri_no, lokasyon, ilgili_talep_no, 
    ilgili_talep_line, talep_yok, talep_var, belge_gelecek, 
    belgeli, odenmedi, mixed_payment_id, toplam_tutar, order_no, po_line_no, 
    po_release_no, po_supp_id, is_checked, activity_seq, kiralik_plaka, 
    hesap_kodu, try_toplam_tutar, rowversion, rowkey, muh_odeme, avans_iadesi, 
    iade_hesap_kodu, personel_virmani, virman_yapilacak_kisi, 
    maas_kesintisi, fatura_no, fatura_id
    
     from odoo_portal_param_tab o, harkt_masraf_giris_line_tab a where param_name='ODOO_SERVER' and masraf_no = masraf_no_ and 
     satir_no=line_no_) LOOP
      req_ := '
        {
          "masraf_no": "'|| rec_.masraf_no||'",
          "satir_no": "'||rec_.satir_no||'",
          "kisi_id": "'|| substr(rec_.kisi_id,2,5)||'",
          "company_id": "'|| rec_.company ||'",
          "bolge": "'|| rec_.bolge||'",
          "bolum": "'|| rec_.bolum||'",
          "durum": "'||  rec_.durum||'",
          "aciklama": "'|| replace(replace(replace(replace(replace(rec_.note_text,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'",
          "proje": "'|| rec_.project_id||'",
          "fis_tarihi": "'|| to_char(rec_.masraf_giris_trh,'yyyy-MM-dd')||'",
          "ongrup_no": "'|| rec_.masraf_on_grup||'",
          "masraf_turu": "'|| rec_.masraf_tipi||'",
          "gider_yeri": "'|| rec_.gider_yeri||'",
          "toplam_tutar": "'|| replace(rec_.toplam_tutar,',','.')||'",
          "try_toplam_tutar": "'|| replace(rec_.try_toplam_tutar,',','.')||'",
          "kdv_orani": "'|| replace(rec_.kdv_orani,',','.')||'",
          "miktar": "'|| replace(rec_.miktar,',','.')||'",
          "currency_code": "'|| rec_.currency||'",
          "tedarikci": "'|| rec_.tedarikci||'",
          "odendi": "'|| rec_.odeme_durum||'",
          "odenmedi": "'|| rec_.odenmedi||'",
          "plaka": "'|| rec_.plaka||'",
          "kiralik": "'|| rec_.kiralik||'",
          "ev_kodu": "'|| rec_.ev_kodu||'",
          "is_emri_no": "'|| rec_.is_emri_no||'",
          "lokasyon": "'|| rec_.lokasyon||'",
          "ilgili_talep_no": "'|| rec_.ilgili_talep_no||'",
          "ilgili_talep_line": "'|| rec_.ilgili_talep_line||'",
          "talep_yok": "'|| rec_.talep_yok||'",
          "talep_var": "'|| rec_.talep_var||'",
          "belge_sonradan": "'|| rec_.belge_gelecek||'",
          "belgeli": "'|| rec_.belgeli||'",
          "belgesiz": "'|| rec_.belge_durum||'",
          "activity_seq": "'|| rec_.activity_seq||'",
          "kiralik_plaka": "'|| replace(replace(replace(replace(replace(rec_.kiralik_plaka,chr(10),' '),chr(13),' '),chr(9),' '),'"',''),'''','')||'",
          "avans_iadesi": "'|| rec_.avans_iadesi||'",
          "iade_hesap_kodu": "'|| rec_.iade_hesap_kodu||'",
          "personel_virmani": "'|| rec_.personel_virmani||'",
          "virman_yapilacak_kisi": "'|| substr(rec_.virman_yapilacak_kisi,2,5)||'",
          "maas_kesintisi": "'|| rec_.maas_kesintisi||'"
        }';
       json_request_ := '{"id":'||'123'||',"jsonrpc":"2.0","method":"call","params":{"service":"object","method":"execute_kw","args":["'||rec_.param_value2||'",'||rec_.param_value3||',"'||rec_.param_value4||'","harkt.masraf.line","write_or_create",['||req_||']]}}';  
       dbms_output.put_line('2.1:'||rec_.param_value||'/jsonrpc');
       http_req:= utl_http.begin_request
                    ( 
                    rec_.param_value||'/jsonrpc'
                    , 'POST'
                    , 'HTTP/1.2'
                    );
                    
        dbms_output.put_line('2.2');
   end loop;
   dbms_output.put_line('3');
   UTL_HTTP.SET_BODY_CHARSET('UTF-8');
   UTL_HTTP.set_header(http_req, 'Connection', 'close');
   UTL_HTTP.set_header(http_req, 'Content-Type', 'application/json');
   UTL_HTTP.set_header(http_req, 'Content-Length', LENGTHB(json_request_));
   UTL_HTTP.write_raw(http_req,UTL_RAW.CAST_TO_RAW(json_request_)); 
   dbms_output.put_line('4');
   http_resp := UTL_HTTP.get_response(http_req);
   dbms_output.put_line('5');
   utl_http.get_header_by_name(http_resp, 'Content-Length', v_len, 1); -- Obtain the length of the response
   json_response := null;
   dbms_output.put_line('Ýstek');
   dbms_output.put_line(json_request_);
   FOR i in 1..CEIL(v_len/32767) -- obtain response in 32K blocks just in case it is greater than 32K
   LOOP
       utl_http.read_text(http_resp, v_txt, case when i < CEIL(v_len/32767) then 32767 else mod(v_len,32767) end);
       json_response := json_response || v_txt; -- build up CLOB
   END LOOP;
   utl_http.end_response(http_resp);
   dbms_output.put_line('Dönüþ');
   dbms_output.put_line(json_response);
   if not json_response like '%"result": true%' then
      error_sys.system_general(masraf_no_||'-'||line_no_||'-'||substr(json_response,1,1900));
   end if;
END masraf_satir_ifs2_odoo;

PROCEDURE Dokuman_Ekle (
   doc_title_ IN VARCHAR2,
   doc_no_ IN OUT VARCHAR2,
   doc_sheet_ IN OUT VARCHAR2,
   doc_rev_ IN OUT VARCHAR2,
   file_name_ IN OUT VARCHAR2,
   ext_ IN VARCHAR2,
   lu_name_ IN VARCHAR2,
   key_ref_ IN VARCHAR2 )
IS
   doc_class_      VARCHAR2(20) := 'RM_MASRAF';
   local_path_out_  VARCHAR2(762);
   start_pos_       NUMBER;
   stop_pos_        NUMBER;
   edm_rep_info_    VARCHAR2(2000);
   tmp_doc_class_   VARCHAR2(36);
   tmp_doc_title_   VARCHAR2(750);
   org_             VARCHAR2(50) := 'ORIGINAL';
   file_type_       VARCHAR2(30);
BEGIN
   doc_rev_       := Doc_Class_Default_API.Get_Default_Value(doc_class_,
                                                                'DocTitle',
                                                                'DOC_REV');
   doc_sheet_     := Doc_Class_Default_API.Get_Default_Value(doc_class_,
                                                                'DocTitle',
                                                                'DOC_SHEET');
   tmp_doc_class_ := doc_class_;
   tmp_doc_title_ := doc_title_;
   Doc_Title_API.Create_Document(tmp_doc_class_,
                                    doc_no_,
                                    doc_sheet_,
                                    doc_rev_,
                                    tmp_doc_title_);
   file_type_ := Edm_Application_API.Get_File_Type(ext_);
   
   IF (file_type_ IS NULL) THEN
      Error_SYS.Appl_General(lu_name_,'NOFILEEXT: There is no file type defined for the file extension :P1',ext_);
   END IF;
   
   Edm_File_API.Create_File_Reference(local_path_out_,
                                     doc_class_,
                                     doc_no_,
                                     doc_sheet_,
                                     doc_rev_,
                                     org_,
                                     file_type_,
                                     NULL,
                                     1 );
   Edm_File_API.Set_File_State(doc_class_,
                              doc_no_,
                              doc_sheet_,
                              doc_rev_,
                              org_,
                              'StartCheckOut',
                              local_path_out_);
   edm_rep_info_ := Edm_File_API.Get_Edm_Repository_Info(doc_class_,
                                                        doc_no_,
                                                        doc_sheet_,
                                                        doc_rev_,
                                                        org_);
   Edm_File_API.Set_File_State(doc_class_,
                                 doc_no_,
                                 doc_sheet_,
                                 doc_rev_,
                                 org_,
                                 'FinishCheckIn',
                                 local_path_out_);
   start_pos_ := instr(edm_rep_info_,Client_SYS.text_separator_||'FILE_NAME=')+11;
   stop_pos_  := instr(edm_rep_info_,Client_SYS.text_separator_,start_pos_);
   file_name_ := substr(edm_rep_info_,start_pos_, stop_pos_ - start_pos_);
   DOC_REFERENCE_OBJECT_API.Create_New_Reference__(lu_name_, key_ref_ ,doc_class_,doc_no_,doc_sheet_,doc_rev_); 
  
END Dokuman_Ekle;

PROCEDURE Dokuman_Sil(
   file_name_ IN  VARCHAR2,
   lu_name_ IN VARCHAR2,
   key_ref_ IN VARCHAR2) 
IS
   CURSOR get_doc_reference IS
   select dr.doc_class, dr.doc_no, dr.doc_sheet, dr.doc_rev from doc_reference_object_tab dr, doc_title_tab dt where dr.lu_name= lu_name_ and dr.key_ref = key_ref_
   and dt.title = file_name_ and dt.doc_class = dr.doc_class and dt.doc_no = dr.doc_no;
   doc_class_ varchar2(200);
   doc_no_ varchar2(200);
   doc_sheet_ varchar2(200);
   doc_rev_ varchar2(200);
BEGIN
   OPEN get_doc_reference;
   FETCH get_doc_reference INTO doc_class_, doc_no_, doc_sheet_, doc_rev_;
   CLOSE get_doc_reference;
   
   
   delete from doc_reference_object_tab where doc_class = doc_class_ and doc_no = doc_no_ and doc_sheet = doc_sheet_ and doc_rev = doc_rev_;
   delete from edm_file_tab f where f.doc_class = doc_class_ and f.doc_no = doc_no_ and f.doc_sheet = doc_sheet_ and f.doc_rev= doc_rev_;
   delete from doc_title_tab t where t.doc_class = doc_class_ and t.doc_no = doc_no_;
   delete from doc_issue_tab f where f.doc_class = doc_class_ and f.doc_no = doc_no_ and f.doc_sheet = doc_sheet_ and f.doc_rev= doc_rev_;
END Dokuman_Sil;


PROCEDURE Para_Talebi_Set_Iptal(Talep_id_ IN VARCHAR2 )
IS
   
   PROCEDURE Cust(Talep_id_ IN VARCHAR2 )
   IS
      info_  VARCHAR2(2000);
      attr_  VARCHAR2(2000);
      
      CURSOR Masraf_Exists IS
       SELECT DISTINCT 1 
         FROM harkt_masraf_giris_line a, harkt_para_talep b
         where a.ilgili_talep_no = b.talep_id
         and b.talep_id = talep_id_
         AND harkt_masraf_giris_api.Get_Durum_Db(a.masraf_no) != 'IPTAL'
       ;
       Masraf_Exists_ NUMBER; 
      
   BEGIN
      
      
   FOR  rec_ in ( SELECT  * 
                   from harkt_para_talep pt
                  where pt.talep_id = talep_id_                
                  )
      LOOP               
   
      IF rec_.DURUM_DB = 'ODENDI' OR rec_.DURUM_DB = 'ODENECEK' THEN
            error_sys.system_general('Odendi / Odenecek statusundeki talepleri iptal edemezsiniz!');
      END IF;    
      
      OPEN Masraf_Exists;
      FETCH Masraf_Exists INTO Masraf_Exists_;
      CLOSE Masraf_Exists;   
      
      IF Masraf_Exists_ = 1 THEN
         error_sys.system_general('Masrafa bagli olan bir talep iptal edilemez! Once bagli masrafi iptal ediniz!');
      END IF;   
         
      FOR arec_ IN (SELECT * FROM approval_routing a
                   WHERE a.key_ref LIKE '%'||talep_id_||'%')
      LOOP
   
      approval_routing_api.Remove__(info_       => info_,
                                    objid_      => arec_.objid,
                                    objversion_ => arec_.objversion,
                                    action_     => 'DO');
      END LOOP;
        
      
   client_sys.Clear_Attr(attr_ );
   client_sys.Add_To_Attr('DURUM_DB','IPTAL',attr_);
   client_sys.Add_To_Attr('ODOO','Y',attr_);
   HARKT_PARA_TALEP_API.MODIFY__(info_       => info_,
                                 objid_      => rec_.objid,
                                 objversion_ => rec_.objversion,
                                 attr_       => attr_,
                                 action_     => 'DO');
   
   END LOOP;
   END Cust;

BEGIN
   Cust(Talep_id_);
END Para_Talebi_Set_Iptal;

PROCEDURE Masraf_Set_Yayinlandi(Masraf_No_ IN VARCHAR2 )
IS
   
   PROCEDURE Cust(Masraf_No_ IN VARCHAR2 )
   IS
      info_  VARCHAR2(2000);
      attr_  VARCHAR2(2000);
      odeme_durum_   VARCHAR2(20);
      pers_virman_durum_ VARCHAR2(20);
      --talep_ok_ NUMBER;
      --masraf_durum_  VARCHAR2(2000);
      
      --CURSOR talep_durum_ IS
      --select 1 from harkt_masraf_giris_line a
      --where a.masraf_no = masraf_no_
      --and harkt_para_talep_api.Get_Durum_Db(a.ilgili_talep_no) = 'YAYINLANDI'
      --;
      
         CURSOR check_odeme_ IS
         SELECT 1
           FROM harkt_masraf_giris_line a
           where a.masraf_no = masraf_no_
           AND a.ODEME_DURUM = 'TRUE' ;
      
      CURSOR check_pers_virman_ IS
         SELECT 1
           FROM harkt_masraf_giris_line a
           where a.masraf_no = masraf_no_
           AND a.PERSONEL_VIRMANI = 'TRUE' 
            ;  
      
      BEGIN
    
         OPEN check_odeme_;
         FETCH check_odeme_ INTO odeme_durum_;
         CLOSE check_odeme_;
         
         IF odeme_durum_ = 1 THEN
         Harkt_Talep_Masraf_Util_Api.Create_Para_Talep_For_Masraf(Masraf_No_);  
         END IF;
         
         OPEN check_pers_virman_;
         FETCH check_pers_virman_ INTO pers_virman_durum_;
         CLOSE check_pers_virman_; 
   
         IF pers_virman_durum_ = 1 THEN
         Harkt_Masraf_Giris_Line_Api.Create_Talep_For_Avans_Trans(Masraf_No_);
         END IF;
         
            FOR lrec_ IN ( SELECT * FROM HARKT_MASRAF_GIRIS_LINE x WHERE x.MASRAF_NO = masraf_no_ AND x.ACTIVITY_SEQ IS NULL )
            
            LOOP   
               --IF lrec_.ACTIVITY_SEQ IS NULL THEN
                  Error_SYS.Record_General('HarktMasrafGiris', 'RELEASACT: Activite No zorunludur.Lutfen Secim yapiniz.');
               --END IF;  
                       
            END LOOP;  
         IF (pers_virman_durum_ = 0 OR pers_virman_durum_ IS NULL) AND (odeme_durum_ = 0 OR odeme_durum_ IS NULL) THEN
            --Error_SYS.Record_General(lu_name_, 'xxxxx');
         FOR  rec_ in ( SELECT  * 
                        FROM harkt_masraf_giris mg
                        WHERE mg.masraf_no = masraf_no_ 
                        )
            LOOP        
                
            
         client_sys.Clear_Attr(attr_ );
         client_sys.Add_To_Attr('DURUM_DB','YAYINLANDI',attr_);
         client_sys.Add_To_Attr('ODOO','Y',attr_);
         HARKT_MASRAF_GIRIS_API.MODIFY__(info_       => info_,
                                         objid_      => rec_.objid,
                                         objversion_ => rec_.objversion,
                                         attr_       => attr_,
                                         action_     => 'DO');
   
         END LOOP;
         END IF;
   END Cust;

BEGIN
   Cust(Masraf_No_);
END Masraf_Set_Yayinlandi;

PROCEDURE Masraf_Set_Iptal(Masraf_No_ IN VARCHAR2 )
IS
   
   PROCEDURE Cust(Masraf_No_ IN VARCHAR2 )
   IS
      info_  VARCHAR2(2000);
      attr_  VARCHAR2(2000);
      statu_check_ VARCHAR2(2000);
   BEGIN   
      
   FOR  rec_ in ( SELECT  * 
                       FROM harkt_masraf_giris mg
                      WHERE mg.masraf_no = masraf_no_ 
                    )
      LOOP           
          FOR irec_ IN (SELECT * FROM harkt_masraf_giris_line a
                       where a.masraf_no = masraf_no_)
          LOOP
        IF irec_.mixed_payment_id is null then    
   
           
      client_sys.Clear_Attr(attr_ );
      client_sys.Add_To_Attr('DURUM_DB','IPTAL',attr_);
      client_sys.Add_To_Attr('ODOO','Y',attr_);
      HARKT_MASRAF_GIRIS_API.MODIFY__(info_       => info_,
                                      objid_      => rec_.objid,
                                      objversion_ => rec_.objversion,
                                      attr_       => attr_,
                                      action_     => 'DO');
            IF irec_.ilgili_talep_no is not null and irec_.talep_yok = 'TRUE' THEN
            statu_check_ := harkt_para_talep_api.Get_Durum_Db(irec_.ilgili_talep_no);
            IF statu_check_ NOT IN ('ODENECEK','ODENDI') THEN
               Odoo_portal_api.para_talebi_Set_Iptal(irec_.ilgili_talep_no);  
            ELSE
               error_sys.system_general('Ilgili para talep statusu, masrafi iptal etmek icin uygun degildir!');            
            END IF;  
         END IF;
        ELSE
          error_sys.system_general('Fisi olusturulan bir masrafi iptal edemezsiniz! Once Fisi iptal ediniz.');  
        END IF;  
           END LOOP;
          
       END LOOP;     
      
   END Cust;

BEGIN
   Cust(Masraf_No_);
END Masraf_Set_Iptal;

PROCEDURE Init
IS
BEGIN
   NULL;
END Init;

BEGIN
   Init;
END Odoo_Portal_Api;
/
