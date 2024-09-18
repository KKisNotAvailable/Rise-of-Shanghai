* This program is extracting the necessary parts (for running FMM) of original files.

*******
** 1 **
*******
* from AA_tradevolatility_master.do (where the entire program starts)
global dropbox "D:/User_Data/Desktop/研究資料/HWT/Rise of Shanghai/replicate_fmm"
global dir "$dropbox/Structural Estimation"
global dir_data "$dropbox/Data"
global dir_data_raw "$dir_data/raw"
global dir_data_primary "$dir_data/primary"
/* global dir_data_secondary "$dir_data/secondary" */
global dir_scratch "$dir_data/scratch"
/* global dir_figures "$dropbox/Figures" */
/* global dir_tables "$dropbox/Tables" */
/* global dir_setup "$dropbox/setup" */
global date = "081721"
cd "$dir"

set maxvar 120000, perm

local regeninputs = 1 // default = 0
local redo_highwaydistance = 1 // default = 0 => 在 distance_081721.do 裡面會用到
* row 80-97
if `regeninputs' == 1{

    // 下面的檔案我覺得 1~68 (產出"$dir_scratch/ICRISAT_croplevel_red17crops_clean_$date.dta") 
    // & 229~340 (產出"$dir_scratch/ICRISAT_latlong_$date.dta" & "$dir_scratch/ICRISAT_latlong_BiggestCity_$date.dta") 
    // 應該就可以
	/* do "1_clean_ICRISATonly_fillmissings_8_17_2021.do"  */

		* Calculating the highway distance between Indian districts - also generated Fig 2
		* Distance between districts is calculated from digitised images of the Indian highway network. Recalculation is --
		* suppressed. To recompute, set flag to 1 (details in README).    
		
		* local redo_highwaydistance = 0 // DEFAULT
		include "distance_081721.do" // note that this calls distance_081721.m SYNCED

		* 產出的 district_distance_dist{s}_081721.dta 裡面的 "s" 代表非高速公路的速限 (5,10,15,20,30)
}

****************
** some notes **
****************
/*
1. [待辦] 每個code file產出的檔案列個清單 (我們所需的即可)

2. 圖檔似乎沒有在code裡面進行調整對齊，所以應該是在存成tif的時候就已經確定邊境的位置差不多了
   關於這點，我們要再看看中國的地圖有沒有已經有完好的shape圖檔 (對照基準)，這樣即使真的需要拿地圖轉成我們需要的檔案也比較方便
   -> 目前關於如何對齊，應該拿shape當base，然後地圖檔轉成黑白之後 (map1)，看map1如何project到base上，再用那個projection function
      去把地圖轉過去再resize即可 (大小align)。
   -> actually, the way they aligned the maps maybe was by fixing 
      lon and lat?

3. 1_clean_ICRISATonly_...8_17_2021.do要修改，因為沒有ICRISAT_croplevel_red17crops.dta
   沒辦法直接按下去跑。(那個檔案是rerun setup裡面的VDSA得到的)
   -> 其實好像這個檔案可以直接不要了。

4. 發現其實直接do distance_081721.do就好了，只是需要先
   4-1. [待辦] 確認../Data/raw/district_geoloc.dta裡面的資料無誤 (一個一個去看谷哥地圖，先用python轉成好貼的型態)
   4-2. [待辦] 看看最終產出的資料 district_distance_dist`d'_${date}.dta 裡面unique的地點跟coords跟我們產出的有無相符
   -> 阿如果都可以的話就直接把 distance_081721.do 裡面抓的資料改名吧 (注意使用欄位的名稱也要一致)

5. 產出的東西不會有具體的path吧?!應該只有花的時間 (distance in hour)
*/