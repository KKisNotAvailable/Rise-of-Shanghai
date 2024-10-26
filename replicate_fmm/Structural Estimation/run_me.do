* This program is extracting the necessary parts (for running FMM) of original files.
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
local redo_highwaydistance = 0 // default = 0 => 在 distance_081721.do 裡面會用到，要重跑 matlab 部分就要改成 1
* the following is approx. row 80-97 in the original file.
if `regeninputs' == 1{

	do "1_clean_ICRISATonly_fillmissings_8_17_2021.do" 

		* Calculating the highway distance between Indian districts - also generated Fig 2
		* Distance between districts is calculated from digitised images of the Indian highway network. Recalculation is --
		* suppressed. To recompute, set flag to 1 (details in README).    
		
		* local redo_highwaydistance = 0 // DEFAULT
		include "distance_081721.do" // note that this calls distance_081721.m SYNCED
}

****************
** some notes **
****************
/*
1. 產出檔案列表
   1_clean_..._2021.do
     - $dir_scratch/ICRISAT_latlong_$date.dta
     - $dir_scratch/ICRISAT_latlong_BiggestCity_$date.dta 
       (row 78 79 uncommented 後可以跟上面那個檔案疊起來，得到 bigcity + all districts)
   distance_081721.do 之一
     - $dir_scratch/district_location_${date}.dta (中繼檔案，留 distinct state-district pair 的)
     - $dir_scratch/district_distance_${date}.dta (用上一個檔案做出 coord pair)
     - $dir_scratch/coor.out (用上一個檔案做的，給matlab讀取用)
   distance_081721.m
     - 畫路網圖
     - $dir_data_primary/distances_offhighwayspeed`d'_${date}.out (就是最終產出的檔案，餵回去Stata的)
   distance_081721.do 之二
   - $dir_data_primary/district_distance_dist`d'_${date}.dta 
     (用不同的一般道路速限 d 產出的 pairwise distance in hours，另外也有直線距離 in miles)

2. 圖檔似乎沒有在code裡面進行調整對齊，所以應該是在存成tif的時候就已經確定邊境的位置了
   -> 目前關於如何對齊，應該拿shape當base，然後地圖檔轉成黑白之後 (map1)，看map1如何project到base上，
      再用那個projection function去把地圖轉過去再resize即可 (大小align)。
   -> actually, the way they aligned the maps maybe was by fixing long and lat?

3. 檔案修改項目
   1_clean_ICRISATonly_fillmissings_8_17_2021.do
     - 因為沒有ICRISAT_croplevel_red17crops.dta沒辦法直接按下去跑。(那個檔案是rerun setup裡面的VDSA得到的)
     - 我只擷取用 district_geoloc.dta 產出 bigcity 的部分 (甚至只保留 bigcity，對我的電腦比較友善)
       大概是原檔案的 row 262-340，有做修改，目的只是為了做出 bigcity subset。
   distance_081721.do
     - 呼叫matlab的時候加了生成.log的指令方便debug
     - 在最上面叫資料點進來的地方可以看要用 bigcity 的 (我自己產的subset，小很多；原 bigcity 檔案是有包括其他districts的)
       或是直接拿geoloc全部下去跑都可以 (只是需要很久)
   distance_081721.m
     - 把 parfor 的部分改回 for，因為電腦記憶體不夠做平行運算。
     - setpath.m 裡面我把一些斜線刪掉，但應該不刪也沒差；還有可以調整平行運算的工人數

4. required packages:
   Stata: ssc install vincenty
   Matlab: Image Processing Toolbox, Parallel Computing Toolboxes
*/