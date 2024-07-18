import sys
import pandas as pd
import time

def main():
    # import our csvs to dataframes and massage data as needed
    df_dns_info = pd.read_csv("dns-info.csv")
    df_dns_info = df_dns_info.drop(columns=['sensor_msg', 'response'])
    df_dns_info = df_dns_info.dropna()

    df_os_info = pd.read_csv("os-info.csv")
    df_os_info = df_os_info.drop(columns=['sensor_msg', 'response'])

    df_chrome_extensions = pd.read_csv("chrome-extensions.csv")
    df_chrome_extensions = df_chrome_extensions.drop(columns=['sensor_msg', 'response'])

    df_ff_addons = pd.read_csv("ff-addons.csv")
    df_ff_addons = df_ff_addons.drop(columns=['sensor_msg', 'response'])

    # Tie the data together
    df_extensions = pd.concat([df_chrome_extensions, df_ff_addons])
    df_extensions = pd.merge(df_extensions, df_dns_info, on=['device_id', 'device_name'], how='left')
    df_extensions = pd.merge(df_extensions, df_os_info, on=['device_id', 'device_name'], how='left')

    # re-sort by device_id
    df_extensions = df_extensions.sort_values(by=['device_id'])

    # Cool. Let's export to CSV now
    timestamp = time.strftime("%Y%m%d-%H%M%S")  # create a timestamp for our filename
    df_extensions.to_csv('browser-extensions-' + timestamp + '.csv', index=False)


if __name__ == "__main__":
    sys.exit(main())

