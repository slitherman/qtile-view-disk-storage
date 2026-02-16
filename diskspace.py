import os 
import subprocess
from libqtile.widget import base
from libqtile import qtile
import threading

def find_drives_by_name(**args):
    """
    This is a special function used to locate the indicies of drives(SSD,HDD,etc.) by their given name
    """
    pass

disk_data_result = None

def run_df():
    global disk_data_result 
    disk_info = subprocess.check_output(["df", "-h"], text=True)
    print(disk_info)
    disk_data_result = disk_info 
    return disk_info


def start_df_thread():
    thread = threading.Thread(target=run_df)
    thread.start()
    return thread

def split_df_into_records():
    """This helper method parses the df output and returns nested dicts within a list where header values are mapped to their respective values"""
    fixed_header_list = []
    record_list = []
    thread = start_df_thread()
    thread.join()

    #df_output = run_df().strip().split("\n")
    df_output = disk_data_result.strip().split("\n")
    header_row = df_output[0]
    headers = header_row.split()

    fixed_header_list = []
    for head in headers:
        if head != "Mounted" and head != "on":
            fixed_header_list.append(head)
        if head == "Mounted":
            mnt = "Mounted_on"
            if mnt not in headers:
                fixed_header_list.append(mnt)

    data_rows = df_output[1:]
    header_len = len(fixed_header_list)
    for i in data_rows:
        newline = i.split()
        if len(newline) == header_len: 
            header_data_pair = zip(fixed_header_list,newline)
            data_dict = dict(header_data_pair)
            record_list.append(data_dict)
        if len(newline) != header_len:
            continue
    validate_records = all(len(record) == header_len for record in record_list)
    
    return record_list
        
#print(split_df_into_records())

def get_ssd_data_by_idx() -> dict:
    get_df_output = split_df_into_records()
    key = "Filesystem"
    value = "/dev/nvme0n1p3"
    for idx in get_df_output:
        if idx[key] == value:
            return idx
    
#print(get_ssd_data_by_idx())

def get_hhd_by_idx() -> dict:
    get_df_output = split_df_into_records()
    key = "Filesystem"
    value = '/dev/sda1'
    for idx in get_df_output:
        if idx[key] == value:
            return idx
#print(get_hhd_by_idx())    


def format_displayed_ssd_data():
    storage_icon = "\uf0c7 "
    data_display_lst = []
    ssd_disk_data = get_ssd_data_by_idx() 

    ssd_disk_data["Filesystem"] = "SSD"
    data_display_lst.append(ssd_disk_data["Filesystem"])
    data_display_lst.append(ssd_disk_data["Used"])
    data_display_lst.append(ssd_disk_data["Avail"])
    data_display_lst.insert(0,storage_icon)
    data_display_lst.insert(2,"-")
    data_display_lst.insert(4,"/")
    data_display_str = " ".join(data_display_lst)
    return data_display_str

def format_displayed_hdd_data():
    storage_icon = "\uf0c7 "
    data_display_lst = []
    hdd_disk_data = get_hhd_by_idx()

    hdd_disk_data["Filesystem"] = "HDD"
    data_display_lst.append(hdd_disk_data["Filesystem"])
    data_display_lst.append(hdd_disk_data["Used"])
    data_display_lst.append(hdd_disk_data["Avail"])
    data_display_lst.insert(0,storage_icon)
    data_display_lst.insert(2,"-")
    data_display_lst.insert(4,"/")
    data_display_str = " ".join(data_display_lst)
    return data_display_str

def display_ssd_and_hdd_data():
    formatted_data_lst = []
    formatted_ssd_data = format_displayed_ssd_data()
    formatted_hdd_data = format_displayed_hdd_data()
    formatted_data_lst.append(formatted_ssd_data)
    formatted_data_lst.append(formatted_hdd_data)
    formatted_data_lst.insert(2, " ")
    formatted_data_str = " ".join(formatted_data_lst)
    return formatted_data_str


class Diskspace(base.InLoopPollText):

    def __init__(self, **config):
            super().__init__("", **config)
            self.ssd = get_ssd_data_by_idx()
            self.hdd = get_hhd_by_idx()
            self.list_of_drives = []
            self.list_of_drives.append(self.ssd)
            self.list_of_drives.append(self.hdd)
            self.drives = self.list_of_drives
            self.add_defaults(Diskspace.defaults)
            self.mouse_callbacks = {"Button1": 
                                    self.swap_drive_display}
           
    defaults = [
         ("devices", [], 
          "Block devices to monitor (e.g sda). Multiple devices can get montirored, and swapped between using mouseclick events. "),
        ]     
    def return_drive(self) -> str:
       if not self.drives:
           return None
       return self.drives[0].get("Filesystem")

    def swap_drive_display(self):
        if len(self.drives) > 1:
            self.drives[0],self.drives[1] =   self.drives[1], self.drives[0]
            self.update(self.poll())
            self.draw()
    
    def poll(self):
        drive = self.return_drive()
        if drive == '/dev/nvme0n1p3':
            self.text = " " + format_displayed_ssd_data() + " "
            return self.text
        if drive == '/dev/sda1':
            self.text = " " +format_displayed_hdd_data() + " "
            return self.text

        self.text = "no data"
        return self.text
    