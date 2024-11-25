* This program is extracting the necessary parts (for running FMM) of original files.
* from AA_tradevolatility_master.do (where the entire program starts)

global dropbox "D:/User_Data/Desktop/研究資料/HWT/Rise of Shanghai/replicate_fmm"
global dir "$dropbox/For_China"
global dir_data "$dropbox/Data"
global dir_data_raw "$dir_data/raw"
global dir_data_primary "$dir_data/primary"
/* global dir_data_secondary "$dir_data/secondary" */
global dir_scratch "$dir_data/scratch"
/* global dir_figures "$dropbox/Figures" */
/* global dir_tables "$dropbox/Tables" */
/* global dir_setup "$dropbox/setup" */
global date = "110924"
cd "$dir"

set maxvar 120000, perm
local redo_highwaydistance = 1 // default = 0 => 在 distance_081721.do 裡面會用到，要重跑 matlab 部分就要改成 1
include "distance_110924.do" // note that this calls distance_081721.m SYNCED


****************
** some notes **
****************
/*
1. 產出檔案列表
   ## From Python ##
     - $dir_scratch/China_customs.dta (從python處理完所有shapefile & top_ports_lon_lat.xlsx產出的)
   distance_081721.do 之一
     - $dir_scratch/custom_distance_${date}.dta (把China_customs.dta裡的各點做配對)
     - $dir_scratch/coor.out (用上一個檔案做的，給matlab讀取用)
   distance_110924.m
     - $dir_data_primary/bilateral_travel_time_China_${date}.out (就是最終產出的pairwise distance in hours，餵回去Stata的)
   distance_110924.do 之二
   - $dir_data_primary/final_result_${date}.dta
     (custom_distance_${date}.dta 跟 bilateral_travel_time_China_${date}.out 整合起來，再另算直線距離 in km)

2. 檔案修改項目
   distance_081721.do
     - 呼叫matlab的時候加了生成.log的指令方便debug
   distance_081721.m
     - 把 parfor 的部分改回 for，因為電腦記憶體不夠做平行運算。
     - setpath.m 可以調整平行運算的工人數

3. required packages:
   Stata: ssc install vincenty
   Matlab: Image Processing Toolbox, Parallel Computing Toolboxes
*/