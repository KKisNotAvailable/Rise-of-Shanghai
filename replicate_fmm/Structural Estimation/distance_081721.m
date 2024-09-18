% This m-file calculates the distance between all districts using the
% various highway maps

% written by Treb on 10/14/14

clear
clc

% set paths
setpath

% Loading the raw (geo-coded) maps
%    cd ..
    
    % India outline
        india_data = imread(strcat(dir_data_raw,'India - outline.tif'));
        in_india = max(india_data,[],3)==0;
        
    % filter rules
        avg_filt = 10; % size of square where you take the average value
        size_filt = 0.025; % what percent of pixels have to be "on" to count an area as "on"
        temp_filter = fspecial('gaussian',[avg_filt,avg_filt]);

    % 2011 data(I now use open street map, but it looks very similar to
    % actual 2011 atlas which we have)
        roads_2011_data = (imread(strcat(dir_data_raw,'India - highways 2011-OSM.tif')));

%         % getting each type of road
% 
%             % highways are orange, red, or purple
%             
%                 % just the outline
%                     highways_outline = double(roads_2011_data(:,:,1)>=0 & roads_2011_data(:,:,1)<=60 & ...
%                         roads_2011_data(:,:,2)>=0 & roads_2011_data(:,:,2)<=30 & ...
%                         roads_2011_data(:,:,3)>=0 & roads_2011_data(:,:,3)<=30 & ...
%                         roads_2011_data(:,:,1)-roads_2011_data(:,:,2)>15 & ...
%                         abs(roads_2011_data(:,:,2)-roads_2011_data(:,:,3))<20);
%                     
%                     % only want the roads with black nearby
%                         temp_filter = fspecial('gaussian',[10,10]);
%                         highways_outline = imfilter(highways_outline,temp_filter,'replicate'); 
%                         temp_filter2 = fspecial('disk',10);
%                         highways_outline = imfilter(highways_outline,temp_filter2,'replicate'); 
%                         highways_outline = highways_outline.*in_india;   
% 
%                 % orange     
% 
%                     highways_orange = double(roads_2011_data(:,:,1)>=20 & roads_2011_data(:,:,1)<=100 & ...
%                         roads_2011_data(:,:,2)>=0 & roads_2011_data(:,:,2)<=80 & ...
%                         roads_2011_data(:,:,3)>=0 & roads_2011_data(:,:,3)<=80 & ...
%                         roads_2011_data(:,:,1)-roads_2011_data(:,:,2)>30 & ...
%                         roads_2011_data(:,:,2)-roads_2011_data(:,:,3)>10 & ...
%                         abs(roads_2011_data(:,:,2)-roads_2011_data(:,:,3))<50);
% %                     
%                         temp_filter = fspecial('gaussian',[2,2]);
%                         highways_orange = imfilter(highways_orange,temp_filter,'replicate'); 
%                         temp_filter2 = fspecial('disk',10);
%                         highways_orange = imfilter(highways_orange,temp_filter2,'replicate'); 
%                         highways_orange = highways_orange.*in_india;
%                 % here are the roads
%                     highways = double(((highways_orange.*highways_outline)>0.000075));        

            highways = double(roads_2011_data(:,:,1)==250);
            temp_filter2 = fspecial('disk',1);
            highways = imfilter(highways,temp_filter2,'replicate');
            highways = double(highways>0);
            imagesc(highways)
                
        % renaming
            highways_2011 = highways;
            tiny_roads_2011 = zeros(size(highways_2011)); % NEED TO FIX IF WE WANT TO USE THESE
            med_roads_2011 = zeros(size(highways_2011)); % NEED TO FIX IF WE WANT TO USE THESE
            roads_2011 = (highways + tiny_roads_2011 + med_roads_2011)>0;
        
    % 2004 data
        roads_2004_data = (imread(strcat(dir_data_raw,'India - highways 2004.tif')));

        % getting each type of road

            % highways are orange
                highways = double(roads_2004_data(:,:,1)==255 & roads_2004_data(:,:,2)==173 & roads_2004_data(:,:,3)==26) + ...
                     double(roads_2004_data(:,:,1)==0 & roads_2004_data(:,:,2)==255 & roads_2004_data(:,:,3)==105) + ... % bright green 
                     double(roads_2004_data(:,:,1)==0 & roads_2004_data(:,:,2)==255 & roads_2004_data(:,:,3)==255) + ... % bright blue
                     double(roads_2004_data(:,:,1)==166 & roads_2004_data(:,:,2)==180 & roads_2004_data(:,:,3)==247); % purple
                temp_filter2 = fspecial('disk',7);
                highways = imfilter(highways,temp_filter2,'replicate'); 
                highways = highways>0; 
                highways = highways.*in_india;
                
            % medium roads are red 
                med_roads = double(roads_2004_data(:,:,1)==255 & roads_2004_data(:,:,2)==69 & roads_2004_data(:,:,3)==101);
                med_roads = imfilter(med_roads,temp_filter,'replicate'); 
                med_roads = med_roads>size_filt; 
                med_roads = med_roads.*in_india.*(1-highways);        
                
            % tiny roads are fuscia
                tiny_roads = double(roads_2004_data(:,:,1)==255 & roads_2004_data(:,:,2)==18 & roads_2004_data(:,:,3)==255);
                tiny_roads  = imfilter(tiny_roads ,temp_filter,'replicate'); 
                tiny_roads  = tiny_roads >size_filt; 
                tiny_roads  = tiny_roads.*in_india.*(1-med_roads-highways);                  
                
        % renaming
            highways_2004 = highways;
            tiny_roads_2004 = tiny_roads;
            med_roads_2004 = med_roads;
            roads_2004 = (highways + tiny_roads + med_roads)>0;
            
    % 1996 data
        roads_1996_data = (imread(strcat(dir_data_raw,'India - highways 1996.tif')));

        % getting each type of road
            
            % highways are orange-ish
                highways = double(roads_1996_data(:,:,1)>=200 & roads_1996_data(:,:,1)<=250 & ...
                    roads_1996_data(:,:,2)>=110 & roads_1996_data(:,:,2)<=200 & ...
                    roads_1996_data(:,:,3)>=80 & roads_1996_data(:,:,3)<=180 & ...
                    roads_1996_data(:,:,1)-roads_1996_data(:,:,2)>30 & ...
                    roads_1996_data(:,:,2)-roads_1996_data(:,:,3)>20);
                temp_filter = fspecial('gaussian',[10,10]);
                highways = imfilter(highways,temp_filter,'replicate'); 
                temp_filter2 = fspecial('disk',8);
                highways = imfilter(highways,temp_filter2,'replicate'); 
                highways = highways>0.02; 
                highways = highways.*in_india;
                
            % medium roads are red 
                med_roads = double(roads_1996_data(:,:,1)>=200 & roads_1996_data(:,:,1)<=240 & ...
                    roads_1996_data(:,:,2)>=120 & roads_1996_data(:,:,2)<=170 & ...
                    abs(roads_1996_data(:,:,2)-roads_1996_data(:,:,3))<10);
                med_roads = imfilter(med_roads,temp_filter,'replicate'); 
                med_roads = med_roads>size_filt; 
                med_roads = med_roads.*in_india.*(1-highways);     
                
            % tiny roads are fuscia
                tiny_roads = double(roads_1996_data(:,:,1)>=200 & roads_1996_data(:,:,1)<=240 & ...
                    roads_1996_data(:,:,2)>=130 & roads_1996_data(:,:,2)<=170 & ...
                    (roads_1996_data(:,:,3)-roads_1996_data(:,:,2))>10);
                tiny_roads  = imfilter(tiny_roads ,temp_filter,'replicate'); 
                tiny_roads  = tiny_roads >size_filt; 
                tiny_roads  = tiny_roads.*in_india.*(1-med_roads-highways);   
                
        % renaming
            highways_1996 = highways;
            tiny_roads_1996 = tiny_roads;
            med_roads_1996 = med_roads;
            roads_1996 = (highways + tiny_roads + med_roads)>0;
    
    % 1988 data
        roads_1988_data = (imread(strcat(dir_data_raw,'India - highways 1988.tif')));

        % getting each type of road
            
            % highways are dark red
                highways = double(roads_1988_data(:,:,1)>=155 & ...
                    (roads_1988_data(:,:,1)-roads_1988_data(:,:,2))>70 & ...
                    (roads_1988_data(:,:,3)-roads_1988_data(:,:,2))>0);
                temp_filter = fspecial('gaussian',[10,10]);
                highways = imfilter(highways,temp_filter,'replicate'); 
                highways = medfilt2(highways,[5,5]); 
                temp_filter2 = fspecial('disk',10);
                highways = imfilter(highways,temp_filter2,'replicate'); 
                highways = highways>0.035; 
                highways = highways.*in_india;
                
            % medium roads are orange 
                med_roads = double(roads_1988_data(:,:,1)>=220 & ...
                    (roads_1988_data(:,:,1)-roads_1988_data(:,:,2))>70 & ...
                    (roads_1988_data(:,:,2)-roads_1988_data(:,:,3))>40);
                med_roads = imfilter(med_roads,temp_filter,'replicate'); 
                med_roads = med_roads>size_filt; 
                med_roads = med_roads.*in_india.*(1-highways);     
                
            % tiny roads are brownish
                tiny_roads = double(roads_1988_data(:,:,1)<=205 & roads_1988_data(:,:,1)>=170 &...
                    roads_1988_data(:,:,2)<=190 & roads_1988_data(:,:,2)>=120 &...
                    roads_1988_data(:,:,3)<=190 & roads_1988_data(:,:,3)>=120 &...
                    (roads_1988_data(:,:,2)-roads_1988_data(:,:,3))>0 & ...
                    (roads_1988_data(:,:,1)-roads_1988_data(:,:,2))>30 & ...
                    (roads_1988_data(:,:,2)-roads_1988_data(:,:,3))<30);
                tiny_roads  = imfilter(tiny_roads ,temp_filter,'replicate'); 
                tiny_roads  = tiny_roads >size_filt; 
                tiny_roads  = tiny_roads.*in_india.*(1-med_roads-highways);   

            % renaming
                highways_1988 = highways;
                tiny_roads_1988 = tiny_roads;
                med_roads_1988 = med_roads;
                roads_1988 = (highways + tiny_roads + med_roads)>0;
    
    % 1977 data
        roads_1977_data = (imread(strcat(dir_data_raw,'India - highways 1977.tif')));

        % getting each type of road
            
            % highways are dark red
                highways = double(roads_1977_data(:,:,1)>=155 & ...
                    roads_1977_data(:,:,2)>=90 & roads_1977_data(:,:,2)<=130 & ...
                    roads_1977_data(:,:,3)>=70 & roads_1977_data(:,:,3)<=120 & ...
                    (roads_1977_data(:,:,1)-roads_1977_data(:,:,2))>70 & ...
                    (roads_1977_data(:,:,2)-roads_1977_data(:,:,3))>0);
                temp_filter = fspecial('gaussian',[10,10]);
                highways = imfilter(highways,temp_filter,'replicate'); 
                highways = medfilt2(highways,[5,5]); 
                temp_filter2 = fspecial('disk',10);
                highways = imfilter(highways,temp_filter2,'replicate'); 
                highways = highways>0.015; 
                highways = highways.*in_india;
                
            % medium roads are orange 
                med_roads = double(roads_1977_data(:,:,1)>=220 & ...
                    (roads_1977_data(:,:,1)-roads_1977_data(:,:,2))>40 & ...
                    (roads_1977_data(:,:,2)-roads_1977_data(:,:,3))>40);
                med_roads = imfilter(med_roads,temp_filter,'replicate'); 
                med_roads = med_roads>size_filt; 
                med_roads = med_roads.*in_india.*(1-highways);     
                
            % tiny roads are brownish
                tiny_roads = double(roads_1977_data(:,:,1)<=170 & roads_1977_data(:,:,1)>=100 &...
                    roads_1977_data(:,:,2)<=150 & roads_1977_data(:,:,2)>=100 &...
                    roads_1977_data(:,:,3)<=120 & roads_1977_data(:,:,3)>=90 &...
                    (roads_1977_data(:,:,2)-roads_1977_data(:,:,3))>0 & ...
                    (roads_1977_data(:,:,1)-roads_1977_data(:,:,2))>0 & ...
                    (roads_1977_data(:,:,2)-roads_1977_data(:,:,3))<30);
                tiny_roads  = imfilter(tiny_roads ,temp_filter,'replicate'); 
                tiny_roads  = tiny_roads >size_filt; 
                tiny_roads  = tiny_roads.*in_india.*(1-med_roads-highways);   

            % renaming
                highways_1977 = highways;
                tiny_roads_1977 = tiny_roads;
                med_roads_1977 = med_roads;
                roads_1977 = (highways + tiny_roads + med_roads)>0;

   % 1969 data
        roads_1969_data = (imread(strcat(dir_data_raw,'India - highways 1969.tif')));

        % getting each type of road
            
            % highways are dark red
                highways = double(roads_1969_data(:,:,1)>=200 & ...
                    roads_1969_data(:,:,2)>=70 & roads_1969_data(:,:,2)<=120 & ...
                    roads_1969_data(:,:,3)>=70 & roads_1969_data(:,:,3)<=120 & ...
                    (roads_1969_data(:,:,1)-roads_1969_data(:,:,2))>70);
                temp_filter = fspecial('gaussian',[10,10]);
                highways = imfilter(highways,temp_filter,'replicate'); 
                highways = medfilt2(highways,[5,5]); 
                temp_filter2 = fspecial('disk',10);
                highways = imfilter(highways,temp_filter2,'replicate'); 
                highways = highways>0.01; 
                highways = highways.*in_india;
                
            % medium roads are orange 
                med_roads = double(roads_1969_data(:,:,1)>=220 & ...
                    (roads_1969_data(:,:,1)-roads_1969_data(:,:,2))>40 & ...
                    (roads_1969_data(:,:,2)-roads_1969_data(:,:,3))>40);
                med_roads = imfilter(med_roads,temp_filter,'replicate'); 
                med_roads = med_roads>size_filt; 
                med_roads = med_roads.*in_india.*(1-highways);     
                
            % tiny roads are brownish
                tiny_roads = double(roads_1969_data(:,:,1)<=190 & roads_1969_data(:,:,1)>=150 &...
                    roads_1969_data(:,:,2)<=160 & roads_1969_data(:,:,2)>=120 &...
                    roads_1969_data(:,:,3)<=140 & roads_1969_data(:,:,3)>=90 &...
                    (roads_1969_data(:,:,2)-roads_1969_data(:,:,3))>0 & ...
                    (roads_1969_data(:,:,1)-roads_1969_data(:,:,2))>0 & ...
                    (roads_1969_data(:,:,2)-roads_1969_data(:,:,3))<50);
                tiny_roads  = imfilter(tiny_roads ,temp_filter,'replicate'); 
                tiny_roads  = tiny_roads >size_filt; 
                tiny_roads  = tiny_roads.*in_india.*(1-med_roads-highways);   

            % renaming
                highways_1969 = highways;
                tiny_roads_1969 = tiny_roads;
                med_roads_1969 = med_roads;
                roads_1969 = (highways + tiny_roads + med_roads)>0;

   % 1962 data
        roads_1962_data = (imread(strcat(dir_data_raw,'India - highways 1962.tif')));

        % getting each type of road
            
            % highways are dark red
                highways = double(roads_1962_data(:,:,1)>=120 & ...
                    roads_1962_data(:,:,1)<=180 & ...
                    roads_1962_data(:,:,2)>=70 & roads_1962_data(:,:,2)<=130 & ...
                    roads_1962_data(:,:,3)>=70 & roads_1962_data(:,:,3)<=130 & ...
                    (roads_1962_data(:,:,1)-roads_1962_data(:,:,2))>30 & ...
                    (roads_1962_data(:,:,2)-roads_1962_data(:,:,3))<25 & ...
                    (roads_1962_data(:,:,2)-roads_1962_data(:,:,3))>-10);
                temp_filter = fspecial('gaussian',[10,10]);
                highways = imfilter(highways,temp_filter,'replicate'); 
                highways = medfilt2(highways,[5,5]); 
                temp_filter2 = fspecial('disk',10);
                highways = imfilter(highways,temp_filter2,'replicate'); 
                highways = highways>0.015; 
                highways = highways.*in_india;
                
            % medium roads are orange 
                med_roads = double(roads_1962_data(:,:,1)>=220 & ...
                    (roads_1962_data(:,:,1)-roads_1962_data(:,:,2))>40 & ...
                    (roads_1962_data(:,:,2)-roads_1962_data(:,:,3))>40);
                med_roads = imfilter(med_roads,temp_filter,'replicate'); 
                med_roads = med_roads>size_filt; 
                med_roads = med_roads.*in_india.*(1-highways);     
                
            % tiny roads are brownish
                tiny_roads = double(roads_1962_data(:,:,1)<=190 & roads_1962_data(:,:,1)>=150 &...
                    roads_1962_data(:,:,2)<=160 & roads_1962_data(:,:,2)>=120 &...
                    roads_1962_data(:,:,3)<=140 & roads_1962_data(:,:,3)>=90 &...
                    (roads_1962_data(:,:,2)-roads_1962_data(:,:,3))>0 & ...
                    (roads_1962_data(:,:,1)-roads_1962_data(:,:,2))>0 & ...
                    (roads_1962_data(:,:,2)-roads_1962_data(:,:,3))<50);
                tiny_roads  = imfilter(tiny_roads ,temp_filter,'replicate'); 
                tiny_roads  = tiny_roads >size_filt; 
                tiny_roads  = tiny_roads.*in_india.*(1-med_roads-highways);   

            % renaming
                highways_1962 = highways;
                tiny_roads_1962 = tiny_roads;
                med_roads_1962 = med_roads;
                roads_1962 = (highways + tiny_roads + med_roads)>0;
                
                
% Converting to speed images
    speed_highway = 4;
    speed_med = 1;
    speed_small = 1;
    speed_india = 1;
    speed_elsewhere = 0;
    
    speed_2011 = (speed_highway.*highways_2011 + speed_med.*med_roads_2011 + speed_small.*tiny_roads_2011)+(1-roads_2011).*in_india*speed_india + (1-in_india)*speed_elsewhere;
    speed_2004 = (speed_highway.*highways_2004 + speed_med.*med_roads_2004 + speed_small.*tiny_roads_2004)+(1-roads_2004).*in_india*speed_india + (1-in_india)*speed_elsewhere;
    speed_1996 = (speed_highway.*highways_1996 + speed_med.*med_roads_1996 + speed_small.*tiny_roads_1996)+(1-roads_1996).*in_india*speed_india + (1-in_india)*speed_elsewhere;
    speed_1988 = (speed_highway.*highways_1988 + speed_med.*med_roads_1988 + speed_small.*tiny_roads_1988)+(1-roads_1988).*in_india*speed_india + (1-in_india)*speed_elsewhere;
    speed_1977 = (speed_highway.*highways_1977 + speed_med.*med_roads_1977 + speed_small.*tiny_roads_1977)+(1-roads_1977).*in_india*speed_india + (1-in_india)*speed_elsewhere;
    speed_1969 = (speed_highway.*highways_1969 + speed_med.*med_roads_1969 + speed_small.*tiny_roads_1969)+(1-roads_1969).*in_india*speed_india + (1-in_india)*speed_elsewhere;
    speed_1962 = (speed_highway.*highways_1962 + speed_med.*med_roads_1962 + speed_small.*tiny_roads_1962)+(1-roads_1962).*in_india*speed_india + (1-in_india)*speed_elsewhere;
    
    
    % Making an image, year by year
    cd(dir_figures)
    
            figure(1)
                clf
                temp_l = 900;
                temp_r = 3750;
                temp_map = [1 1 1; 0.9 0.9 0.9; 0 0 1; 0 1 0; 1 0 0];
                colormap(temp_map)
                imagesc(speed_1962(:,temp_l:temp_r))
                axis off
                print road_network_1962.eps -depsc 
                
            figure(1)
                clf
                temp_l = 900;
                temp_r = 3750;
                temp_map = [1 1 1; 0.9 0.9 0.9; 0 0 1; 0 1 0; 1 0 0];
                colormap(temp_map)
                imagesc(speed_1962(:,temp_l:temp_r))
                axis off
                print road_network_1969.eps -depsc 
                
            figure(1)
                clf
                temp_l = 900;
                temp_r = 3750;
                temp_map = [1 1 1; 0.9 0.9 0.9; 0 0 1; 0 1 0; 1 0 0];
                colormap(temp_map)
                imagesc(speed_1977(:,temp_l:temp_r))
                axis off
                print road_network_1977.eps -depsc
                
            figure(1)
                clf
                temp_l = 900;
                temp_r = 3750;
                temp_map = [1 1 1; 0.9 0.9 0.9; 0 0 1; 0 1 0; 1 0 0];
                colormap(temp_map)
                imagesc(speed_1988(:,temp_l:temp_r))
                axis off
                print road_network_1988.eps -depsc
                
            figure(1)
                clf
                temp_l = 900;
                temp_r = 3750;
                temp_map = [1 1 1; 0.9 0.9 0.9; 0 0 1; 0 1 0; 1 0 0];
                colormap(temp_map)
                imagesc(speed_1996(:,temp_l:temp_r))
                axis off
                print road_network_1996.eps -depsc
                
            figure(1)
                clf
                temp_l = 900;
                temp_r = 3750;
                temp_map = [1 1 1; 0.9 0.9 0.9; 0 0 1; 0 1 0; 1 0 0];
                colormap(temp_map)
                imagesc(speed_2004(:,temp_l:temp_r))
                axis off
                print road_network_2004.eps -depsc
                
            figure(1)
                clf
                temp_l = 900;
                temp_r = 3750;
                temp_map = [1 1 1; 0.9 0.9 0.9; 0 0 1; 0 1 0; 1 0 0];
                colormap(temp_map)
                imagesc(speed_2011(:,temp_l:temp_r))
                axis off
                print road_network_2011.eps -depsc
    
    % making an image
        figure(1)
            clf
            temp_map = [1 1 1; 0.9 0.9 0.9; 0 0 1; 0 1 0; 1 0 0];
            temp_l = 900;
            temp_r = 3750;
            colormap(temp_map)

            subplot(3,3,1)
                imagesc(speed_1962(:,temp_l:temp_r))
                axis off
                title('1962')

            subplot(3,3,2)
                imagesc(speed_1969(:,temp_l:temp_r))
                axis off
                title('1969')
                
            subplot(3,3,3)
                imagesc(speed_1977(:,temp_l:temp_r))
                axis off
                title('1977')
                
            subplot(3,3,4)
                imagesc(speed_1988(:,temp_l:temp_r))
                axis off
                title('1988')    
                
            subplot(3,3,5)
                imagesc(speed_1996(:,temp_l:temp_r))
                axis off
                title('1996')    
                
            subplot(3,3,6)
                imagesc(speed_2004(:,temp_l:temp_r))
                axis off
                title('2004')   
                                      
            subplot(3,3,8)
                imagesc(speed_2011(:,temp_l:temp_r))
                axis off
                title('2011') 
                
        print road_network.eps -depsc 
        print road_network.png -dpng
        print road_netword.pdf -dpdf

%% Calculating distances

% cd 'Distance calculations'
cd(dir_structural)

for s = [20,15,30,5,10]

    % Converting to speed images
        speed_highway = 60; % speed limit on highways
        speed_med = s; % speed limit on state highways
        speed_small = s; % speed limit on smaller (paved) roads
        speed_india = s; % speed limit on unpaved roads / off-road
        speed_elsewhere = s*0.25; % speed limit elsewhere
        
        speed_2011 = (speed_highway.*highways_2011 + speed_med.*med_roads_2011 + speed_small.*tiny_roads_2011)+(1-roads_2011).*in_india*speed_india + (1-in_india)*speed_elsewhere;
        speed_2004 = (speed_highway.*highways_2004 + speed_med.*med_roads_2004 + speed_small.*tiny_roads_2004)+(1-roads_2004).*in_india*speed_india + (1-in_india)*speed_elsewhere;
        speed_1996 = (speed_highway.*highways_1996 + speed_med.*med_roads_1996 + speed_small.*tiny_roads_1996)+(1-roads_1996).*in_india*speed_india + (1-in_india)*speed_elsewhere;
        speed_1988 = (speed_highway.*highways_1988 + speed_med.*med_roads_1988 + speed_small.*tiny_roads_1988)+(1-roads_1988).*in_india*speed_india + (1-in_india)*speed_elsewhere;
        speed_1977 = (speed_highway.*highways_1977 + speed_med.*med_roads_1977 + speed_small.*tiny_roads_1977)+(1-roads_1977).*in_india*speed_india + (1-in_india)*speed_elsewhere;
        speed_1969 = (speed_highway.*highways_1969 + speed_med.*med_roads_1969 + speed_small.*tiny_roads_1969)+(1-roads_1969).*in_india*speed_india + (1-in_india)*speed_elsewhere;
        speed_1962 = (speed_highway.*highways_1962 + speed_med.*med_roads_1962 + speed_small.*tiny_roads_1962)+(1-roads_1962).*in_india*speed_india + (1-in_india)*speed_elsewhere;


    % Converting from latitude and longitude to coordinate of the pixel

            % here are the locations of each edge of the image (according to
            % arcgis)
                % ugh, despite all its proclamations, here's actually what gis exported: 
                coor_bottom = 6.786;
                coor_top = 35.249;
                coor_left = 59.298;
                coor_right = 106.209;

            % it's a little tricky, because we're using the image convention of
            % coordinates
                data_coor = load(strcat(dir_scratch,'coor.out'));
                orig_x = data_coor(:,1);
                orig_y = data_coor(:,2);
                dest_x = data_coor(:,3);
                dest_y = data_coor(:,4);

                X = size(highways_2004,1); % north / south (higher X indicates further south)
                Y = size(highways_2004,2); % east / west (higher Y indicates further east)
                orig_pix = NaN(size(orig_x,1),2);
                dest_pix = NaN(size(orig_x,1),2);
                orig_pix(:,1) = ceil(X*((coor_top - orig_y)./(coor_top-coor_bottom))); % how much toward the top
                dest_pix(:,1) = ceil(X*((coor_top - dest_y)./(coor_top-coor_bottom))); % how much toward the top
                orig_pix(:,2) = ceil(Y*((orig_x - coor_left)./(coor_right-coor_left))); % how much toward the west
                dest_pix(:,2) = ceil(Y*((dest_x - coor_left)./(coor_right-coor_left))); % how much toward the west

           % double checking that we have it right
%                 figure(1)
%                     clf
%                     hold on
%                     surf(in_india,'edgecolor','none')
%                     view(2)
%                     scatter(orig_pix(:,2),orig_pix(:,1))
%             
            
            
    %%% Estimating the cost via each mode of travel from every origin to every
    %%% destination
        image_X = size(highways_2004,2);
        image_Y = size(highways_2004,1);
    
    % Loading the program we use to calculate distance 
        getd = @(p)path(p,path);

        % accurate fast marching (for 2d)
            getd(strcat(dir_structural,'/FastMarching_version3b/code'));
            % getd('C:\Users\Treb Allen\Dropbox\Research\Trade\Topography\Simulations\Accurate fast marching');
            % h = waitbar(0,'Calculating distances');

            N = size(data_coor,1); % number of bilateral pairs
            [temp_coor,temp_IA,temp_IC] = unique(orig_pix,'rows');
            K = size(temp_coor,1)
            disp('calculating distances')
        
            % want to normalize units by width of country
                unit_norm = 1734 / size(speed_2004,1); % this should give you approximate hours of driving time

                temp_dist = cell(K);
                
           %  parpool(30)  
            % parfor i = 1:K % my computer seems having memory limitation to do parellel computing.
            for i = 1:K
                
                i

                % here are the coordinates 
                    temp_orig_y_2 = temp_coor(i,1);
                    temp_orig_x_2 = temp_coor(i,2);

                % 1962
                    temp_t_1962 = msfm(unit_norm*ones(size(speed_1962)).*speed_1962, [temp_orig_y_2;temp_orig_x_2], true, true);    
                
                % 1969
                    temp_t_1969 = msfm(unit_norm*ones(size(speed_1969)).*speed_1969, [temp_orig_y_2;temp_orig_x_2], true, true);     
               
                % 1977
                    temp_t_1977 = msfm(unit_norm*ones(size(speed_1977)).*speed_1977, [temp_orig_y_2;temp_orig_x_2], true, true);   
                    
                % 1988
                    temp_t_1988 = msfm(unit_norm*ones(size(speed_1988)).*speed_1988, [temp_orig_y_2;temp_orig_x_2], true, true);  
                
                % 1996
                    temp_t_1996 = msfm(unit_norm*ones(size(speed_1996)).*speed_1996, [temp_orig_y_2;temp_orig_x_2], true, true);  
                
                % 2004
                    temp_t_2004 = msfm(unit_norm*ones(size(speed_2004)).*speed_2004, [temp_orig_y_2;temp_orig_x_2], true, true);  
                                          
                % 2004
                    temp_t_2011 = msfm(unit_norm*ones(size(speed_2011)).*speed_2011, [temp_orig_y_2;temp_orig_x_2], true, true);  
                
                % saving the distances
                    temp_loc = find(orig_pix(:,1)==temp_coor(i,1) & orig_pix(:,2)==temp_coor(i,2)); % all destinations      
                     temp_dist{i}=[temp_loc, temp_t_1962(sub2ind(size(temp_t_1977),dest_pix(temp_loc,1),dest_pix(temp_loc,2))),...
                        temp_t_1969(sub2ind(size(temp_t_1977),dest_pix(temp_loc,1),dest_pix(temp_loc,2))),... 
                        temp_t_1977(sub2ind(size(temp_t_1977),dest_pix(temp_loc,1),dest_pix(temp_loc,2))),...
                         temp_t_1988(sub2ind(size(temp_t_1977),dest_pix(temp_loc,1),dest_pix(temp_loc,2))),...
                         temp_t_1996(sub2ind(size(temp_t_1977),dest_pix(temp_loc,1),dest_pix(temp_loc,2))),...
                         temp_t_2004(sub2ind(size(temp_t_1977),dest_pix(temp_loc,1),dest_pix(temp_loc,2))),...
                         temp_t_2011(sub2ind(size(temp_t_1977),dest_pix(temp_loc,1),dest_pix(temp_loc,2)))];
            end
            
            
            % putting the distances back into the the correct order
                    dist_1962 = NaN(size(data_coor,1),1);
                    dist_1969 = NaN(size(data_coor,1),1);
                    dist_1977 = NaN(size(data_coor,1),1);
                    dist_1988 = NaN(size(data_coor,1),1);
                    dist_1996 = NaN(size(data_coor,1),1);
                    dist_2004 = NaN(size(data_coor,1),1);
                    dist_2011 = NaN(size(data_coor,1),1);
                for i=1:K
                    temp_treb = temp_dist{i};
                    temp_loc = temp_treb(:,1);
                    dist_1962(temp_loc) = temp_treb(:,2);
                    dist_1969(temp_loc) = temp_treb(:,3);
                    dist_1977(temp_loc) = temp_treb(:,4);
                    dist_1988(temp_loc) = temp_treb(:,5);
                    dist_1996(temp_loc) = temp_treb(:,6);
                    dist_2004(temp_loc) = temp_treb(:,7);
                    dist_2011(temp_loc) = temp_treb(:,8);
                end
            
%% exporting the data to stata
    temp = [dist_1962, dist_1969, dist_1977, dist_1988, dist_1996, dist_2004, dist_2011];
    filename = strcat(dir_data_primary,'distances_offhighwayspeed',num2str(s),data_version,'.out');
    save(filename,'temp','-ascii','-tabs')
    
end
    

disp('hi!')
    