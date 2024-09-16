*** This is the first of the do files that processes data from the VDSA master files

clear
cap log close
set more off
use "$dir_data_raw/ICRISAT_croplevel_red17crops.dta", clear

	gen decade = string(10*floor((year)/10))  /* e.g. 1970-1979 is 1970 */
	replace District="SANTHAL PARGANAS" if District=="DUMKA" 

*this was phubani in icrisat data and bad merges means it shoudl still be
	replace District="PHULBANI" if District=="KANDHAMAL" 
	replace District="NORTH ARCOT" if District=="NORTH ARCOT-AMBEDKAR" 
	replace District="NORTH ARCOT" if District=="VELLORE" 

*1967 missing below
	expand 2 if District=="MALAPPURAM" & year==1966, generate(newbie)
	replace year=1967 if newbie==1

	foreach var of varlist totgeog- cufalow {
		replace `var'=. if newbie==1 
	}

	drop newbie
	
*two obs here for 1999
preserve
	keep  if year==1999 & District=="SINGBHUM"
	foreach var of varlist price-dec {
		egen m`var'=max(`var') if year==1999 & District=="SINGBHUM",by(crop)
		replace `var'=m`var' if `var'==. & year==1999 & District=="SINGBHUM" 
		drop m`var'
	}
	replace soiltype="USTALF/USTOLLS - 100%" if year==1999 & dist=="SINGBHUM" & state=="BIHAR" 
	drop if year==1999 & District=="SINGBHUM" & state=="JHARKHAND" 
	save "$dir_scratch/tempdhksfhasf.dta", replace
restore

	drop  if year==1999 & District=="SINGBHUM"
	append using "$dir_scratch/tempdhksfhasf.dta"

*now we have a rectangular data set 
*some manual cleans
	replace District="BILASPUR (MADHYA PRADESH)" if District=="BILASPUR (CHHATTISGARH)" 
	replace District="RAIGARH (MADHYA PRADESH)" if District=="RAIGARH (CHHATTISGARH)" 
	replace State="MADHYA PRADESH" if District=="RAIGARH (MADHYA PRADESH)" 
	replace State="MADHYA PRADESH" if District=="BILASPUR (MADHYA PRADESH)" 
	replace State="UTTAR PRADESH" if State=="UTTARANCHAL"
	replace State="MADHYA PRADESH" if State=="CHHATTISGARH"
	replace State="BIHAR" if State=="JHARKHAND"

	***paddy price fix
	gen Xpricepaddy=price if crop=="Paddy"
	egen pricepaddy=max(Xpricepaddy),by(State District year)
	replace pricepaddy=. if crop!="Rice"
	drop Xpricepaddy
	drop if crop=="Paddy"
	gen paddypriceratio= pricepaddy/price
	egen meanppr_sd=mean(paddypriceratio),by(State decade)
	egen meanppr_d=mean(paddypriceratio),by(decade)
	egen meanppr=mean(paddypriceratio)
	replace price=pricepaddy/meanppr_sd if pricepaddy!=. & price==. & crop=="Rice"
	replace price=pricepaddy/meanppr_d if pricepaddy!=. & price==. & crop=="Rice"
	replace price=pricepaddy/meanppr if pricepaddy!=. & price==. & crop=="Rice"

	*now save teh clean file
	sort State District crop year
save "$dir_scratch/ICRISAT_croplevel_red17crops_clean_$date.dta", replace

*************************************************************

* above is 1~68, no change

***************
*** 229~340 ***
***************
use "$dir_scratch/ICRISAT_croplevel_red17crops_clean_$date.dta", clear
	keep year District State  lat longv
	rename lat latitude
	rename longv longitude
	sort latitude longitude
	egen tag=tag(District State) if latitude!=. & longitude!=.
	keep if tag==1
	drop tag year

	*email pointed out errors in VDSA data
	replace lat=12.683333 if State=="TAMIL NADU" & District=="CHENGALPATTU M.G.R."  // based on Chengalpattu wiki
	replace longitude=79.983333 if State=="TAMIL NADU" & District=="CHENGALPATTU M.G.R."

	replace lat=22.6 if State=="MADHYA PRADESH" & District=="MANDLA"  // based on mandla town wiki
	replace longitude=80.38 if State=="MADHYA PRADESH" & District=="MANDLA"

	replace lat=26.56 if State=="MADHYA PRADESH" & District=="BHIND"  // based on district capital wiki 
	replace longitude=78.79 if State=="MADHYA PRADESH" & District=="BHIND"

	replace lat=11.75 if State=="TAMIL NADU" & District=="SOUTH ARCOT"  // based on Culldelore wiki
	replace longitude=79.75 if State=="TAMIL NADU" & District=="SOUTH ARCOT"


	replace lat=21.94 if State=="ORISSA" & District=="MAYURBHANJ"  // based Baripada wiki
	replace longitude=86.72 if State=="ORISSA" & District=="MAYURBHANJ"

	replace lat=16.994444 if State=="MAHARASHTRA" & District=="RATNAGIRI"  // based Baripada wiki
	replace longitude=73.3 if State=="MAHARASHTRA" & District=="RATNAGIRI"

* Using google API to figure out location of each district
	ren District district
	ren State state

preserve
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
	save "$dir_scratch/district_geoloc_${date}.dta", replace
restore

	sort state district
	merge m:1 state district using "$dir_scratch/district_geoloc_${date}.dta"   // , keep(match master)
	tab _merge
	drop _merge
	vincenty latitude longitude latitude_google longitude_google, v(distance_check)

	replace latitude_google=. if district=="SANTHAL PARGANAS"   
	replace longitude_google=. if district=="SANTHAL PARGANAS" 

*% DGA 02/10/21: google tend to be better so use them. I think perhaps the icrisat are nearest rain station.
	replace latitude=latitude_google if latitude_google!=.
	replace longitude=longitude_google if longitude_google!=.
	drop longitude_google latitude_google distance_check
	ren district District
	ren state State
	
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
