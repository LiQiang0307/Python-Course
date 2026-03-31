'''
Author: LiQiang
Date: 2026-02-11 19:41:45
LastEditors: LiQiang
LastEditTime: 2026-02-11 19:42:00
Description: 文件描述
'''
for i in range(1,10):
    for j in range(1,i+1):
        print(str(j)+"x" + str(i)+"="+str(i*j)+"\t",end=" ")
    print('')