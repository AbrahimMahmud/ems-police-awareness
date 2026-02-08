require(foreign)
require(ggplot2)
require(MASS)
# library('Rcpp'); # Package for Mark
# library(fixest) # Package for Mark

db_path = 'C:/Users/meita/Dropbox (MIT)/NEMSIS Data/'
# db_path <- '/Users/mbrenn/Dropbox (MIT)/NEMSIS Paper' # Path for mark

setwd(db_path)
dat_1 <- read.csv('Data/NEMSIS/Pre-processed/220202_refactored_outer_merge/220208_daily_zip_call_maj_div_0.csv')
dat_2<- read.csv('Data/NEMSIS/Pre-processed/220202_refactored_outer_merge/220208_daily_zip_call_maj_div_1.csv')

dat <- bind_rows(dat_1, dat_2) # **MH: Careful: bind_rows binds rows by names (callID, dateID), rbind just jams rows by order (1st column to 1st column, 2nd column to 2nd column, and so on...)
rm(dat_1, dat_2)
#summary(m1 <- glm.nb(daysabs ~ math + prog, data = dat))
fenegbin(total_mh_calls ~ Rank_of_Share_Decile + total_other_calls | newzip + Date, 
         dat, vcov = ~newzip, 
         panel.id=c('newzip', 'Date'))
  
View(dat)

#lets get the data with the added zeros
rm(dat)
dat <- read.csv('Analysis/AWS/220223_regressions/220218_zip_days_w_zeros_0.csv')

