*** This is the first of the do files that processes data from the VDSA master files
* This was extractions from 1_clean_ICRISATonly_fillmissings_8_17_2021.do
* to do basic data cleaning for running FMM, but if we were only testing if FMM
* actually works, this file can be ignored.

* And notice I changed some of the arrangement and variable names to fit the process.
* so it is normal that some of the code is different from the original

clear
cap log close
set more off

use "$dir_data_raw/district_geoloc.dta", clear
	drop if state=="MADHYA PRADESH" & district=="RAIGARH (MADHYA PRADESH)" // this appeared also in chattigarh, last one was correct

	*some manual cleans
	replace district="BILASPUR (MADHYA PRADESH)" if district=="BILASPUR (CHHATTISGARH)" 
	replace district="RAIGARH (MADHYA PRADESH)" if district=="RAIGARH (CHHATTISGARH)" 
	replace state="MADHYA PRADESH" if district=="RAIGARH (MADHYA PRADESH)" 
	replace state="MADHYA PRADESH" if district=="BILASPUR (MADHYA PRADESH)" 
	replace state="UTTAR PRADESH" if state=="UTTARANCHAL"
	replace state="MADHYA PRADESH" if state=="CHHATTISGARH"
	replace state="BIHAR" if state=="JHARKHAND"

	replace latitude_google=. if district=="SANTHAL PARGANAS"   
	replace longitude_google=. if district=="SANTHAL PARGANAS" 

*% DGA 02/10/21: google tend to be better so use them. I think perhaps the icrisat are nearest rain station.
	ren latitude_google latitude
	ren longitude_google longitude
	ren state State
	ren district District
	
	gen StateCapital_lat=.
	replace StateCapital_lat=17.704167  if State=="ANDHRA PRADESH" // Visakhapatnam
	replace StateCapital_lat=26.172222  if State=="ASSAM" // Guwahati
	replace StateCapital_lat=25.6  if State=="BIHAR" | State=="JHARKHAND"  // Patna
	replace StateCapital_lat=23.03  if State=="GUJARAT" // Ahmedabad
	replace StateCapital_lat=28.4211  if State=="HARYANA" // Faridabad
	replace StateCapital_lat=31.103333  if State=="HIMACHAL PRADESH" // Shimla
	replace StateCapital_lat=12.978889  if State=="KARNATAKA" // Bangalore
	replace StateCapital_lat=9.97  if State=="KERALA" // Kochi
	replace StateCapital_lat=22.716667  if State=="MADHYA PRADESH" | State=="CHHATTISGARH" // Indore
	replace StateCapital_lat=18.975  if State=="MAHARASHTRA" // Mumbai
	replace StateCapital_lat=20.27  if State=="ORISSA" // Bubenswart
	replace StateCapital_lat=30.91  if State=="PUNJAB" // lhudiana
	replace StateCapital_lat=26.9  if State=="RAJASTHAN"  // Jaipur
	replace StateCapital_lat=13.082694  if State=="TAMIL NADU"  // chennai
	replace StateCapital_lat=26.449923  if State=="UTTAR PRADESH" | State=="UTTARANCHAL" // Kanpur
	replace StateCapital_lat=22.5726  if State=="WEST BENGAL" // Kolkot8ta

	gen StateCapital_long=.
	replace StateCapital_long=83.297778  if State=="ANDHRA PRADESH"
	replace StateCapital_long=91.745833  if State=="ASSAM"
	replace StateCapital_long=85.1  if State=="BIHAR" | State=="JHARKHAND"
	replace StateCapital_long=72.58  if State=="GUJARAT"
	replace StateCapital_long=77.3078  if State=="HARYANA"
	replace StateCapital_long=77.172222  if State=="HIMACHAL PRADESH"
	replace StateCapital_long=77.591667  if State=="KARNATAKA"
	replace StateCapital_long=76.28  if State=="KERALA"
	replace StateCapital_long=75.847222  if State=="MADHYA PRADESH" | State=="CHHATTISGARH"
	replace StateCapital_long=72.825833  if State=="MAHARASHTRA"
	replace StateCapital_long=85.84  if State=="ORISSA"
	replace StateCapital_long=75.85  if State=="PUNJAB"
	replace StateCapital_long=75.8  if State=="RAJASTHAN"
	replace StateCapital_long=80.270694  if State=="TAMIL NADU"
	replace StateCapital_long=80.331874  if State=="UTTAR PRADESH" | State=="UTTARANCHAL"
	replace StateCapital_long=88.3639  if State=="WEST BENGAL"

save "$dir_scratch/ICRISAT_latlong_$date.dta", replace

	egen tag=tag(State)
	keep if tag==1
	replace District="BIGGEST_CITY"
	drop latitude longitude
	rename StateCapital_lat latitude
	rename StateCapital_long longitude
	append using "$dir_scratch/ICRISAT_latlong_$date.dta"
	drop StateCapital_*
	drop tag
save "$dir_scratch/ICRISAT_latlong_BiggestCity_$date.dta", replace
