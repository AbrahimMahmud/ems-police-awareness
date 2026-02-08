require(foreign)
require(ggplot2)
require(MASS)
# install.packages('fixest')
require(fixest)

db_path = 'C:/Users/meita/Dropbox (MIT)/NEMSIS Data/'
setwd(db_path)
dat_1 <- read.csv('Data/NEMSIS/Pre-processed/220202_refactored_outer_merge/220208_daily_zip_call_maj_div_0.csv')
dat_2<- read.csv('Data/NEMSIS/Pre-processed/220202_refactored_outer_merge/220208_daily_zip_call_maj_div_1.csv')
# 
dat <- rbind(dat_1, dat_2)
rm(dat_1, dat_2)
# #summary(m1 <- glm.nb(daysabs ~ math + prog, data = dat))
# View(dat)

#lets get the data with the added zeros
# rm(dat)
# dat <- read.csv('Analysis/AWS/220223_regressions/220218_zip_days_w_zeros_0.csv')
# View(dat)

#drop unnecessary variables and add in categorical dates
# dat <- subset(dat, select = -c(X))
dat$Date <- as.Date(dat$Date)
dat$weekday <- as.factor(weekdays(dat$Date))
dat$month <- as.factor(months(dat$Date))
dat$year <- as.factor(format(dat$Date, '%Y'))

tweets <- read.csv("Data/Tweets/Pre-processed/220126_final_daily_tweet_count.csv")
tweets <- subset(tweets, select = -c(X))
tweets$day <- as.Date(tweets$date)

merged <- merge(x=dat, y=subset(tweets, select = c('day', 'log_3_day')), by.x = 'Date', by.y = 'day', all.x = TRUE)

rm(dat)

no_nan <- na.omit(merged)

rm(merged)
no_nan$newzip = as.factor(no_nan$newzip)

zip_info <- read.csv("/home/ec2-user/220223_regressions/220218_zip_div_decile_0.csv")

#merge with the zip info file
w_zip_info <- merge(x = no_nan, y = subset(zip_info, select = c('newzip', 'Rank_of_Share_Decile', 'majority_div')), all.x = TRUE, by = 'newzip')
#get the interaction variables
rm(no_nan)
no_nan <- transform(no_nan, interaction = ifelse(Rank_of_Share_Decile == 9, 1, 0))

no_nan <- transform(no_nan, interaction = interaction * log_3_day)


# summary(m1 <- glm.nb(total_mh_calls ~ log_3_day + total_other_calls + interaction
#                   + weekday + month + year, data = w_zip_info))
# gravity_negbin = fenegbin(Euros ~ log(dist_km) | Origin + Destination + Product + Year, trade)

negbin = fenegbin(total_mh_calls ~ log_3_day + total_other_calls +
                    weekday + month + year | newzip, no_nan)

print(negbin)
# m = PanelOLS(dependent=reg.total_mh_calls,
#              exog=reg[['total_other_calls', 'log_3_day', 'interaction', 'weekday','month', 'year']],
#              entity_effects=False,
#              time_effects=False,
#              other_effects=reg['newzip'])
# print(m.fit(cov_type='clustered', clusters=reg['majority_div']))

