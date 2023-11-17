# coding=utf-8
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from sklearn.preprocessing import StandardScaler
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.decomposition import PCA, KernelPCA


def oneHot2index(oneHot):
    return np.array([np.argmax(one) for one in oneHot])

# X = np.load('train_rates2.npy')
# y = np.load('train_y2.npy')
# y = oneHot2index(y)
# print(X.shape)
#
# pca = PCA(n_components=2)
# X_pca = pca.fit(X).transform(X)
#
# # kpca = KernelPCA(kernel="rbf", fit_inverse_transform=True, gamma=10)
# # X_kpca = kpca.fit_transform(X)
# # X_back = kpca.inverse_transform(X_kpca)
# # pca = PCA()
# # X_pca = pca.fit_transform(X)
#
# plt.figure()
# for c, i, target_name in zip("rgb", [0, 1], ['benign', 'malware']):
#     plt.scatter(X_pca[y == i, 0], X_pca[y == i, 1], c=c, label=target_name)
# plt.legend()
# plt.title('dataset')
# plt.show()


# ori = np.load('test_malware_rates.npy')
# adv = np.load('1_5000_0.npz')['adv_x']
# changed = np.load('1_5000_0.npz')['changed']
#
# print(ori.shape)
# print(adv.shape)
# print(changed.shape)
# # 统计哪个feature改变了
# hundards_num = np.zeros(100)
# for example in changed:
#   for i, val in enumerate(example):
#     # 改变了
#     if val != 0:
#       hundards_num[i] = hundards_num[i] + 1
#
# hundards_num = np.array(hundards_num)
# print(hundards_num)
#
# # 统计哪个feature改变了 并且原来是0
# hundards_num_appear = np.zeros(100)
# for j,example in enumerate(changed):
#   for i, val in enumerate(example):
#     # 改变了
#     if val != 0 and ori[j][i] == 0:
#       hundards_num_appear[i] = hundards_num_appear[i] + 1
#
# hundards_num_appear = np.array(hundards_num_appear)
# print(hundards_num_appear)
# print(hundards_num - hundards_num_appear)

# =====fig5==============================================
# fnr/理想
def a():
  pdf = PdfPages('fig8.pdf')

  # rf
  x = [0, 2, 4, 6, 8, 10, 20, 40, 50, 60, 70, 100]
  y = [0.04, 0.058, 0.108, 0.138, 0.152, 0.172, 0.386, 0.8, 0.846, 0.872, 0.878, 0.886]
  plt.plot(x, y, 's--', label='RF', c='#252525')

  # svm
  x = [0,2, 4,6, 8, 10, 20,40,50,60,70,100]
  y = [0.064, 0.868,0.942, 0.958, 0.96, 0.96, 0.96, 0.96,0.96,0.96,0.96,0.96]
  plt.plot(x, y,'d-', label='SVM', c='#252525')

  # knn1
  x = [0,2, 4,6, 8, 10, 20,40,50,60,70,100]
  y = [0.078,0.412, 0.476, 0.488, 0.496, 0.498, 0.574,0.6,0.626,0.744,0.844,0.846]
  plt.plot(x, y,'*:', label='1-NN', c='#252525')

  # knn3
  x = [0,2, 4,6, 8, 10, 20,40,50,60,70,100]
  y = [0.106,0.394, 0.466, 0.478, 0.486, 0.488, 0.548,0.564,0.598,0.79,0.856,0.864]
  plt.plot(x, y,'o-.', label='3-NN', c='#252525')
  plt.ylim(0, 1)
  plt.legend(loc='lower right', fontsize=13)
  plt.xlabel('#  Upper Bound of Modification', fontsize=13)
  plt.ylabel('Evasion Rate', fontsize=14)
  plt.subplots_adjust(left=0.1, bottom=0.10, right=0.99, top=0.98, wspace=0.35, hspace=0.25)
  pdf.savefig()
  plt.close()
  pdf.close()
  plt.show()
# a()
def aqwe():
  pdf = PdfPages('figdefence.pdf')

  # rf
  x = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
  y = [0.6896230805025592, 0.7983721979600195, 0.8225163602096002,
       0.8285655448148355, 0.8308983691172783, 0.8349712018192134,
       0.8355221957404534, 0.8350655625443578, 0.8362134956855549,
       0.8366119236090674]
  plt.plot(x, y, 's--', label='Benign App', c='#252525')

  # svm
  x = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
  y = [0.6396542409508374, 0.8213723179353142, 0.8518439256983477,
       0.8589096643528936, 0.8623990377444594, 0.8666248053103935,
       0.8679626622932571, 0.8678677290070733, 0.8692128114913388,
       0.8693878101147468]
  plt.plot(x, y,'*:', label='Malware', c='#252525')

  plt.ylim(0.6, 1)
  plt.legend(loc='lower right', fontsize=13)
  plt.xlabel('% of Adversarial Examples Added in Training Set', fontsize=13)
  plt.ylabel('F-measure', fontsize=14)
  plt.subplots_adjust(left=0.1, bottom=0.10, right=0.99, top=0.98, wspace=0.35, hspace=0.25)
  pdf.savefig()
  plt.close()
  pdf.close()
  plt.show()
# aqwe()

def adversarial_training():
  pdf = PdfPages('defence-adv.pdf')

  # rf
  x = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
  y = [0.6896230805025592, 0.7983721979600195, 0.8225163602096002,
       0.8285655448148355, 0.8308983691172783, 0.8349712018192134,
       0.8355221957404534, 0.8350655625443578, 0.8362134956855549,
       0.8366119236090674]
  # plt.plot(x, y, 's--', label='Benign App', c='#252525')

  # svm
  x = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
  # y = [0.86, 0.8513723179353142, 0.8318439256983477,
  #      0.8189096643528936, 0.8066990377444594, 0.8023990377444594,
  #      0.7679626622932571, 0.7278677290070733, 0.69,
  #      0.63]
  y = [0.804, 0.6523, 0.5745,
       0.56432, 0.5564, 0.5536,
       0.5535, 0.5553, 0.5532,
       0.551]
  y= np.array(y)
  y = y * 100
  plt.plot(x, y, 's-', label='Malware', c='#252525')

  plt.ylim(40, 90)
  # plt.legend(loc='lower right', fontsize=13)
  plt.xlabel('% of Adversarial Examples Added in Training Set', fontsize=13)
  plt.ylabel('Evasion rate', fontsize=14)
  plt.subplots_adjust(left=0.1, bottom=0.10, right=0.99, top=0.98, wspace=0.35, hspace=0.25)
  pdf.savefig()
  plt.close()
  pdf.close()
  plt.show()
# adversarial_training()

#
# # fnr/实际
# def aa():
#   pdf = PdfPages('fig5_2.pdf')
#
#   # svm
#   x = [0,1.812, 1.996,2.032, 2.036, 2.036, 2.036,2.036,2.036,2.036,2.036,2.036]
#   y = [0.064, 0.868,0.942, 0.958, 0.96, 0.96, 0.96, 0.96,0.96,0.96,0.96,0.96]
#   plt.plot(x, y,'h-',label='SVM')
#
#   # rf
#   x = [0,1.812, 3.556,5.2, 6.784, 8.34, 15.136,21,21.988,22.32,22.356,22.4]
#   y = [0.04,0.058,0.108, 0.138, 0.152, 0.172, 0.386, 0.8,0.846,0.872,0.878,0.886]
#   plt.plot(x, y,'s--', label='RF')
#
#   # knn1
#   x = [0,1.812,2.856, 3.772,4.664, 5.64, 9.688, 16.478,19.464,20.264,20.396,20.576]
#   y = [0.078,0.412, 0.476, 0.488, 0.496, 0.498, 0.574,0.6,0.626,0.744,0.844,0.846]
#   plt.plot(x, y,'*:',label='1-NN')
#
#   # knn3
#   x = [0,1.812, 2.92,3.884, 4.824, 5.748, 10.156,18,21.456,22.464,22.6,22.796]
#   y = [0.106,0.394, 0.466, 0.478, 0.486, 0.488, 0.548,0.564,0.598,0.79,0.856,0.864]
#   plt.plot(x, y,'o-.',label='3-NN')
#   plt.ylim(0, 1)
#   plt.legend(loc='upper center', bbox_to_anchor=(0.85,0.75),fontsize=13)
#   plt.xlabel('Distortion', fontsize=14)
#   plt.ylabel('Evasion Rate', fontsize=14)
#   plt.subplots_adjust(left=0.1, bottom=0.10, right=0.99, top=0.98, wspace = 0.35, hspace = 0.25)
#   pdf.savefig()
#   plt.close()
#   pdf.close()
#   plt.show()
# # aa()


# 实际/理论
def aa():
  pdf = PdfPages('fig8_2.pdf')

  # rf
  x = [0, 2, 4, 6, 8, 10, 20, 40, 50, 60, 70, 100]
  # y = [0, 1.812, 3.556, 5.2, 6.784, 8.34, 15.136, 21, 21.988, 22.32, 22.356, 22.4]
  y = [0, 1.1724, 2.4815, 3.2464, 3.6842, 4.4186, 11.0259, 19.75,21.0922, 22.064, 22.25, 22.51]
  plt.plot(x, y, 's--', label='RF', c='#252525')

  # svm
  x = [0, 2, 4, 6, 8, 10, 20, 40, 50, 60, 70, 100]
  # y = [0,1.812, 1.996,2.032, 2.036, 2.036, 2.036,2.036,2.036,2.036,2.036,2.036]
  y = [0, 1.876, 2.04, 2.11, 2.12, 2.12, 2.12, 2.12, 2.12, 2.12, 2.12, 2.12]
  plt.plot(x, y, 'd-', label='SVM', c='#252525')

  # knn1
  x = [0,2, 4,6, 8, 10, 20,40,50,60,70,100]
  # y = [0,1.812,2.856, 3.772,4.664, 5.64, 9.688, 16.478,19.464,20.264,20.396,20.576]
  y = [0, 1.864, 2.15, 2.246, 2.339, 2.369, 4.3345, 5.2, 6.818, 13.946, 18.635, 18.738]
  plt.plot(x, y, '*:', label='1-NN', c='#252525')

  # knn3
  x = [0,2, 4,6, 8, 10, 20,40,50,60,70,100]
  # y = [0,1.812, 2.92,3.884, 4.824, 5.748, 10.156,18,21.456,22.464,22.6,22.796]
  y = [0, 1.7869, 2.1288, 2.226, 2.32, 2.352, 3.9343, 4.688, 6.9498, 17.9848, 20.836, 21.1667]
  plt.plot(x, y, 'o-.', label='3-NN', c='#252525')
  plt.ylim(0, 25)
  plt.legend(loc='lower right', bbox_to_anchor=(1, 0.1), fontsize=13)
  plt.xlabel('# Upper Bound of Modification', fontsize=13)
  plt.ylabel('# Actual Modification', fontsize=14)
  plt.subplots_adjust(left=0.1, bottom=0.10, right=0.99, top=0.98, wspace=0.35, hspace=0.25)
  pdf.savefig()
  plt.close()
  pdf.close()
  plt.show()
# aa()

#
# # 两两一起
# def aaaa():
#   max_num = [0,2, 4,6, 8, 10, 20,40,50,60,70,100]
#   rf_num = [0, 1.812, 3.556, 5.2, 6.784, 8.34, 15.136, 21, 21.988, 22.32, 22.356, 22.4]
#   svm_num = [0, 1.812, 1.996, 2.032, 2.036, 2.036, 2.036, 2.036, 2.036, 2.036, 2.036, 2.036]
#   knn1_num=[0, 1.812, 2.856, 3.772, 4.664, 5.64, 9.688, 16.478, 19.464, 20.264, 20.396, 20.576]
#   knn3_num=[0, 1.812, 2.92, 3.884, 4.824, 5.748, 10.156, 18, 21.456, 22.464, 22.6, 22.796]
#   rf_fnr = [0.04, 0.058, 0.108, 0.138, 0.152, 0.172, 0.386, 0.8, 0.846, 0.872, 0.878, 0.886]
#   svm_fnr=[0.064, 0.868, 0.942, 0.958, 0.96, 0.96, 0.96, 0.96, 0.96, 0.96, 0.96, 0.96]
#   knn1_fnr=[0.078, 0.412, 0.476, 0.488, 0.496, 0.498, 0.574, 0.6, 0.626, 0.744, 0.844, 0.846]
#   knn3_fnr=[0.106, 0.394, 0.466, 0.478, 0.486, 0.488, 0.548, 0.564, 0.598, 0.79, 0.856, 0.864]
#   num = [rf_num,svm_num,knn1_num,knn3_num]
#   fnr = [rf_fnr,svm_fnr,knn1_fnr,knn3_fnr]
#   for i in range(4):
#     pdf = PdfPages('fig5_new_'+str(i)+'.pdf')
#
#
#     # plt.plot(max_num, fnr[i], 's--', label='Max')
#     # plt.plot(num[i],fnr[i], 'h-', label='Actual')
#     plt.plot(max_num, num[i], 's--', label='Max')
#     # plt.plot(num[i], fnr[i], 'h-', label='Actual')
#
#     # plt.plot(x, y, '*:', label='1-NN')
#     #
#     # plt.plot(x, y, 'o-.', label='3-NN')
#
#     # plt.ylim(0, 1)
#     plt.legend(loc='upper center', bbox_to_anchor=(0.85, 0.75), fontsize=13)
#     # plt.xlabel('Distortion', fontsize=14)
#     # plt.ylabel('Evasion Rate', fontsize=14)
#     plt.subplots_adjust(left=0.1, bottom=0.10, right=0.99, top=0.98, wspace=0.35, hspace=0.25)
#     pdf.savefig()
#     plt.close()
#     pdf.close()
#     exit(2)
#     # plt.show()
# aaaa()
# def aaaaaa():
#   pdf = PdfPages('fig9.pdf')
#   # svm
#   x = [0,2, 4,6, 8, 10, 20,40,50,60,70,100]
#   y = [0.06,0.83, 0.91, 0.92, 0.92, 0.92, 0.92,0.92,0.92,0.92,0.92,0.92]
#   plt.plot(x, y,'h-',label='SVM')
#
#   # rf
#   x = [0,2, 4,6, 8, 10, 20,40,50,60,70,100]
#   y = [0.04,0.05, 0.1, 0.13, 0.15, 0.17, 0.38,0.79,0.84,0.87,0.87,0.87]
#   plt.plot(x, y,'s--', label='RF')
#
#   # knn1
#   x = [0,2, 4,6, 8, 10, 20,40,50,60,70,100]
#   y = [0.08,0.4, 0.47, 0.48, 0.49, 0.49, 0.56,0.58,0.61,0.73,0.83,0.83]
#   plt.plot(x, y,'*:',label='1-NN')
#
#   # knn3
#   x = [0,2, 4,6, 8, 10, 20,40,50,60,70,100]
#   y = [0.11,0.39, 0.46, 0.47, 0.48, 0.48, 0.54,0.55,0.59,0.78,0.84,0.85]
#   plt.plot(x, y,'o-.',label='3-NN')
#   plt.ylim(0, 1)
#   plt.legend(loc='upper center', bbox_to_anchor=(0.85,0.75),fontsize=13)
#   plt.xlabel('Distortion', fontsize=14)
#   plt.ylabel('Evasion Rate', fontsize=14)
#   plt.subplots_adjust(left=0.1, bottom=0.10, right=0.99, top=0.98, wspace = 0.35, hspace = 0.25)
#   pdf.savefig()
#   plt.close()
#   pdf.close()
#   plt.show()


# 柱状图 =========
# import numpy as np
# import matplotlib.pyplot as plt
#
# F_J_RF = np.array([0.04, 0.62, 0.8, 0.72, 0.89])
# F_J_RF_num = np.array([0,36.564,48.264,19.096,22.4])
#
# F_J_SVM = np.array([0.06, 0.75, 0.96, 0.76, 0.96])
# F_J_SVM_num = np.array([0,36.564,48.264,1.42,2.036])
#
# F_J_1NN = np.array([0.08, 0.41, 0.76, 0.7, 0.85])
# F_J_1NN_num = np.array([0, 36.564, 48.264, 25.534, 20.576])
#
# F_J_3NN = np.array([0.11, 0.58, 0.78, 0.7, 0.86])
# F_J_3NN_num = np.array([0, 36.564, 48.264, 25.768, 22.796])
#
# F_C_RF = np.array([0.04, 0.33, 0.1, 1, 1])
# F_C_RF_num = np.array([0, 32.138, 7.322, 88.528, 55.072])
#
# F_C_SVM = np.array([0.06, 0.65, 0.82, 1, 1])
# F_C_SVM_num = np.array([0, 32.138, 7.322, 1.462, 1.608])
#
# F_C_1NN = np.array([0.08, 0.17, 0.12, 0.63, 0.76])
# F_C_1NN_num = np.array([0, 32.138, 7.322, 67.066, 20.002])
#
# F_C_3NN = np.array([0.11, 0.16, 0.14, 0.64, 0.83])
# F_C_3NN_num = np.array([0, 32.138, 7.322, 93.14, 54.374])
#
# P_J_RF = np.array([0.03, 0.58, 0.73, 0.81, 1])
# P_J_RF_num = np.array([0, 976.4, 957.37, 293.72, 196.5])
#
# P_J_SVM = np.array([0.07, 0.27, 0.76, 0.82, 1])
# P_J_SVM_num = np.array([0, 976.4, 957.37, 108.42, 85.14])
#
# P_J_1NN = np.array([0.05, 0.33, 0.47, 0.78, 0.95])
# P_J_1NN_num = np.array([0, 976.4, 957.37, 413.53, 395.6])
#
# P_J_3NN = np.array([0.04, 0.56, 0.67, 0.79, 0.97])
# P_J_3NN_num = np.array([0, 976.4, 957.37, 379.9, 353.82])
#
# P_C_RF = np.array([0.03, 1, 0.99, 1, 1])
# P_C_RF_num = np.array([0, 2422.86, 2349.44, 1284.85, 1284.85])
#
# P_C_SVM = np.array([0.07, 0.91, 0.97, 1, 1])
# P_C_SVM_num = np.array([0, 2422.86, 2349.44, 1798.79, 1798.79])
#
# P_C_1NN = np.array([0.05, 0.92, 0.91, 1, 1])
# P_C_1NN_num = np.array([0, 2422.86, 2349.44, 1578.53, 1578.53])
#
# P_C_3NN = np.array([0.04, 0.96, 0.91, 1, 1])
# P_C_3NN_num = np.array([0, 2422.86, 2349.44, 1431.69, 1431.69])
#
# for [F_J_RF,F_J_RF_num,filename,min,max] in [
# [F_J_RF,F_J_RF_num,'F_J_RF',0,100],
# [F_J_SVM,F_J_SVM_num,'F_J_SVM',0,100],
# [F_J_1NN,F_J_1NN_num,'F_J_1NN',0,100],
# [F_J_3NN,F_J_3NN_num,'F_J_3NN',0,100],
# [F_C_RF,F_C_RF_num,'F_C_RF',0,100],
# [F_C_SVM,F_C_RF_num,'F_C_SVM',0,100],
# [F_C_1NN,F_C_1NN_num,'F_C_1NN',0,100],
# [F_C_3NN,F_C_3NN_num,'F_C_3NN',0,100],
# [P_J_RF,P_J_RF_num,'P_J_RF',0,1000],
# [P_J_SVM,P_J_SVM_num,'P_J_SVM',0,1000],
# [P_J_1NN,P_J_1NN_num,'P_J_1NN',0,1000],
# [P_J_3NN,P_J_3NN_num,'P_J_3NN',0,1000],
# [P_C_RF,P_C_RF_num,'P_C_RF',1000,2700],
# [P_C_SVM,P_C_SVM_num,'P_C_SVM',1000,2500],
# [P_C_1NN,P_C_1NN_num,'P_C_1NN',1000,2500],
# [P_C_3NN,P_C_3NN_num,'P_C_3NN',1000,2500]]:
#   pdf = PdfPages('mama/'+filename+'.pdf')
#   fig = plt.figure()
#   ax1 = fig.add_subplot(2,1,1)
#   size = 2
#   x = np.arange(size)
#
#   plt.ylim(min, max)
#   plt.xticks(fontsize=14)
#   plt.yticks(fontsize=14)
#   # plt.title('Performance on normal data',fontsize=16)
#   plt.ylabel('# of added calls',fontsize=14)
#
#   plt.xlim(0, 50)
#
#   width = 4
#
#   M_x = []
#   for i in range(5):
#       i = i*10+6
#       M_x.append(i)
#   group_labels = ['BaseLine', 'F','FT','FB','FTB']
#   plt.xticks(M_x, group_labels, rotation=0,fontsize=14)
#
#   poses = []
#   for x in M_x:
#     poses.append(x)
#
#   ax1.bar(poses, F_J_RF_num,  width=width, color='#e1e1e1', label='MNIST', ec='black',align='center',
#           ls='-', lw=1)
#
#   # plt.xlabel('Value of K',fontsize=14)
#   # =================
#   ax2 = fig.add_subplot(2,1,2)
#   size = 2
#   x = np.arange(size)
#
#   plt.ylim(0,1)
#   plt.xticks(fontsize=14)
#   plt.yticks(fontsize=14)
#   # plt.title('Performance on normal data',fontsize=16)
#   plt.ylabel('Evasion Rate',fontsize=14)
#   plt.xlim(0, 50)
#   width = 4
#   plt.xticks(M_x, group_labels, rotation=0,fontsize=14)
#
#   poses = []
#   for x in M_x:
#     poses.append(x)
#
#   ax2.bar(poses, F_J_RF,  width=width, color='#e1e1e1', label='MNIST', ec='black',align='center',
#           ls='-', lw=1)
#   plt.xlabel('Senario',fontsize=14)
#
#   pdf.savefig()
#   plt.close()
#   pdf.close()


# ======最大的图 分四组========111111111111

def b():
  F_J_RF = np.array([0.04, 0.62, 0.8, 0.72, 0.89])
  F_J_RF_num = np.array([0,50.29,51.98,25.609,22.5])

  F_J_SVM = np.array([0.06, 0.75, 0.96, 0.76, 0.96])
  F_J_SVM_num = np.array([0,48.3,50.275,1.8783,2.12])

  F_J_1NN = np.array([0.08, 0.61, 0.76, 0.7, 0.85])
  F_J_1NN_num = np.array([0, 48.977, 51.36, 33.69, 18.7376])

  F_J_3NN = np.array([0.11, 0.58, 0.78, 0.7, 0.86])
  F_J_3NN_num = np.array([0, 47.61, 50.5136, 33.289, 21.167])

  F_C_RF = np.array([0.04, 0.562, 0.576, 1, 1])
  F_C_RF_num = np.array([0, 93.6, 94.47, 80.528, 55.072])

  F_C_SVM = np.array([0.06, 0.1, 0.274, 1, 1])
  F_C_SVM_num = np.array([0, 34.73, 23.146, 1.462, 1.608])

  F_C_1NN = np.array([0.08, 0.15, 0.18, 0.63, 0.76])
  F_C_1NN_num = np.array([0, 76.6, 73.5, 106.793, 26.3184])

  F_C_3NN = np.array([0.11, 0.14, 0.16, 0.64, 0.83])
  F_C_3NN_num = np.array([0, 66.1972, 58.5, 144.627, 65.19664])

  P_J_RF = np.array([0.03, 0.58, 0.73, 0.81, 1])
  P_J_RF_num = np.array([0, 1671.2, 1264.3, 362.62, 196.5])

  P_J_SVM = np.array([0.07, 0.27, 0.76, 0.82, 1])
  P_J_SVM_num = np.array([0, 1070.26, 1178.83, 132.22, 85.14])

  P_J_1NN = np.array([0.05, 0.33, 0.47, 0.78, 0.95])
  P_J_1NN_num = np.array([0, 1445.55, 1127.45, 438.92, 304.2947])

  P_J_3NN = np.array([0.04, 0.56, 0.67, 0.79, 0.97])
  P_J_3NN_num = np.array([0, 1725.29, 1291, 421.823, 309.65])

  P_C_RF = np.array([0.03, 1, 0.99, 1, 1])
  P_C_RF_num = np.array([0, 2422.86, 2373.17, 1284.85, 1284.85])

  P_C_SVM = np.array([0.07, 0.91, 0.97, 1, 1])
  P_C_SVM_num = np.array([0, 2662.4835, 2422.1, 1798.79, 1798.79])

  P_C_1NN = np.array([0.05, 0.92, 0.91, 1, 1])
  P_C_1NN_num = np.array([0, 2633.5435, 2581.8, 1578.53, 1578.53])

  P_C_3NN = np.array([0.04, 0.96, 0.91, 1, 1])
  P_C_3NN_num = np.array([0, 2523.8125, 2581.8, 1431.69, 1431.69])

  for index, data in enumerate([
    [
      [F_J_RF, F_J_RF_num, 'F_J_RF', 0, 100],
     [F_J_SVM, F_J_SVM_num, 'F_J_SVM', 0, 100],
     [F_J_1NN, F_J_1NN_num, 'F_J_1NN', 0, 100],
     [F_J_3NN, F_J_3NN_num, 'F_J_3NN', 0, 100]
    ],

    [
      [F_C_RF, F_C_RF_num, 'F_C_RF', 0, 150],
     [F_C_SVM, F_C_SVM_num, 'F_C_SVM', 0, 150],
     [F_C_1NN, F_C_1NN_num, 'F_C_1NN', 0, 150],
     [F_C_3NN, F_C_3NN_num, 'F_C_3NN', 0, 150]
    ],

    [
      [P_J_RF, P_J_RF_num, 'P_J_RF', 0, 1800],
      [P_J_SVM, P_J_SVM_num, 'P_J_SVM', 0, 1800],
      [P_J_1NN, P_J_1NN_num, 'P_J_1NN', 0, 1800],
      [P_J_3NN, P_J_3NN_num, 'P_J_3NN', 0, 1800]
    ],

    [
      [P_C_RF, P_C_RF_num, 'P_C_RF', 1000, 2700],
      [P_C_SVM, P_C_SVM_num, 'P_C_SVM', 1000, 2700],
      [P_C_1NN, P_C_1NN_num, 'P_C_1NN', 1000, 2700],
      [P_C_3NN, P_C_3NN_num, 'P_C_3NN', 1000, 2700]
    ]
  ]):



    fig = plt.figure(figsize=(20, 5))
    pdf = PdfPages('mama_overall_'+str(index)+'.pdf')
    M_x = [m * 10 + 6 for m in range(5)]
    group_labels = ['Base', 'F', 'FT', 'FB', 'FTB']
    poses = [x for x in M_x]
    bar_color = ['white','#e1e1e1','#959595','#505050','#252525']
    width = 4
    x_label = ['(a) RF','(b) SVM', '(c) 1-NN', '(d) 3-NN']
    for i in range(4):
      ax1 = fig.add_subplot(2,4,i+1)
      size = 2
      x = np.arange(size)

      plt.ylim(data[i][3], data[i][4])
      plt.xticks(fontsize=16)
      plt.yticks(fontsize=16)
      # plt.title('Performance on normal data',fontsize=16)
      plt.ylabel('Avg. Distortion', fontsize=16)

      plt.xlim(0, 50)

      plt.xticks(M_x, group_labels, rotation=0, fontsize=16)

      ax1.bar(poses, data[i][1],  width=width, color=bar_color, label='MNIST', ec='black',align='center',
              ls='-', lw=1)
      ax1.plot([11, 11], [data[i][3], data[i][4]], 'm--', c="#e1e1e1")
    # =================
    for i in range(4):
      ax2 = fig.add_subplot(2,4,4+i+1)
      size = 2
      x = np.arange(size)

      plt.ylim(0,1)
      plt.xticks(fontsize=16)
      plt.yticks(fontsize=16)
      # plt.title('Performance on normal data',fontsize=16)
      plt.ylabel('Evasion Rate',fontsize=16)
      plt.xlim(0, 50)
      plt.xticks(M_x, group_labels, rotation=0,fontsize=16)

      ax2.bar(poses[0], data[i][0][0], width=width, color=bar_color[0], label='', ec='black', align='center',
              ls='-', lw=1)
      ax2.bar(poses[1], data[i][0][1], width=width, color=bar_color[1], label='Senario F', ec='black', align='center',
              ls='-', lw=1)
      ax2.bar(poses[2], data[i][0][2], width=width, color=bar_color[2], label='Senario FT', ec='black', align='center',
              ls='-', lw=1)
      ax2.bar(poses[3], data[i][0][3], width=width, color=bar_color[3], label='Senario FB', ec='black', align='center',
              ls='-', lw=1)
      ax2.bar(poses[4], data[i][0][4], width=width, color=bar_color[4], label='Senario FTB', ec='black', align='center',
              ls='-', lw=1)
      ax2.plot([11, 11], [0,1], 'm--',c="#e1e1e1")
      font = {'family': 'Times New Roman',
              'color': 'black',
              'weight': 'normal',
              'size': 21,
              }
      plt.xlabel(x_label[i], font)
    # plt.legend(loc='upper center', bbox_to_anchor=(-1.5, 3), fontsize=20, ncol=4)
    plt.subplots_adjust(left=0.05, bottom=0.13, right=0.99, top=0.96, wspace = 0.35, hspace = 0.25)
    pdf.savefig()
    plt.close()
    pdf.close()
    # plt.show()
# b()

# ======================== 1st paper ========================
# ==========================================
# ||
# || title: trigger size, y:evasion rate, x:poisoning rate
# ||
# ==========================================
def drebin_per_size():
  per_size1 = np.array([0.1,0.2,0.3, 0.4, 0.5, 0.6,0.7, 0.8, 0.9,1.0])
  acc_size1 = 1 - np.array([0.34, 0.13, 0.09, 0.06, 0.06, 0.05, 0.04,0.03,0.03,0.03])
  acc_size1 = acc_size1 * 100

  per_size2 = np.array([0.1,0.2, 0.3,0.4,1.0])
  acc_size2 = 1 - np.array([0.14,0.06,0.06,0.02,0.02])
  acc_size2 = acc_size2 * 100

  per_size3 = np.array([0.1,0.2,0.3,1.0])
  acc_size3 = 1 - np.array([0.12,0.06,0.02,0.02])
  acc_size3 = acc_size3 * 100

  per_size4 = np.array([0.1, 0.2, 0.3,1.0])
  acc_size4 = 1 - np.array([0.11, 0.06, 0.01, 0.01])
  acc_size4 = acc_size4 * 100

  # per_size5 = np.array([0.1, 0.2, 0.3])
  # acc_size5 = np.array([0.11, 0.06, 0.01])

  per_size6 = np.array([0.1, 0.2, 0.3, 1.0])
  acc_size6 = 1 - np.array([0.03, 0.03, 0.02, 0.02])
  acc_size6 = acc_size6 * 100

  # per_size7 = np.array([0.1, 0.2, 0.3])
  # acc_size7 = np.array([0.03, 0.03, 0.02])
  #
  # per_size8 = np.array([0.1, 0.2, 0.3])
  # acc_size8 = np.array([0.02, 0.01, 0.01])
  #
  # per_size8 = np.array([0.1, 0.2, 0.3])
  # acc_size8 = np.array([0.02, 0.01, 0.01])
  #
  # per_size8 = np.array([0.1, 0.2, 0.3])
  # acc_size8 = np.array([0.02, 0.01, 0.01])


  for index, data in enumerate([
    [
     [per_size1, acc_size1],
     [per_size2, acc_size2],
     [per_size3, acc_size3],
     [per_size4, acc_size4],
     [per_size6, acc_size6]
    ]
  ]):

    fig = plt.figure(figsize=(20, 4))
    pdf = PdfPages('drebin_per_size_'+str(index)+'.pdf')

    # title = ['Trigger Size 1', 'Trigger Size 2', 'Trigger Size 3', 'Trigger Size 4&5', 'Trigger Size 6-10']
    title = ['Trigger Size 0.0690%', 'Trigger Size 0.1379%', 'Trigger Size 0.2069%', 'Trigger Size \n0.2759% & 0.3448%', 'Trigger Size \n0.4138%-0.6897%']
    for i in range(5):
      ax1 = fig.add_subplot(1,5,i+1)

      plt.ylim(0, 100)
      plt.xticks(fontsize=12)
      plt.yticks(fontsize=16)
      plt.xlabel('% of poison data in training set', fontsize=16)
      plt.ylabel('Evasion Rate', fontsize=16)

      print(min(data[i][0]), max(data[i][0]))
      plt.xlim(min(data[i][0]), max(data[i][0]))
      print(data[i][0].shape, data[i][1].shape)
      ax1.plot(data[i][0], data[i][1], 'o-.', label='3-NN')

      font = {'family': 'Times New Roman',
              'color': 'black',
              'weight': 'normal',
              'size': 21,
              }
      # plt.xlabel(x_label[i], font)
      plt.title(title[i], font)
    # plt.legend(loc='upper center', bbox_to_anchor=(-1.5, 3), fontsize=20, ncol=4)
    plt.subplots_adjust(left=0.05, bottom=0.2, right=0.99, top=0.84, wspace = 0.35, hspace = 0.25)
    pdf.savefig()
    plt.close()
    pdf.close()
    # plt.show()
# drebin_per_size()

def mama_per_size():
  per_size1 = np.array([0.1,  0.2,  0.3,  0.4,  0.5,  0.6,  0.7,  0.8,  0.9,  1.0,  1.1,  1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 2,    3,    4,   5,   7,   8,    9,    10])
  acc_size1 = 1 - np.array([0.96, 0.96, 0.96, 0.95, 0.93, 0.91, 0.91, 0.72, 0.65, 0.52, 0.41, 0.36, 0.34, 0.26, 0.26, 0.26, 0.25, 0.24, 0.23, 0.1, 0.1, 0.1, 0.06, 0.06, 0.01])
  acc_size1 = acc_size1 * 100

  per_size2 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8])
  acc_size2 = 1 - np.array([0.95, 0.96, 0.94, 0.9, 0.79, 0.45, 0.27, 0.26, 0.21, 0.21, 0.15, 0.15, 0.13, 0.13, 0.13, 0.13, 0.06, 0.03])
  acc_size2 = acc_size2 * 100

  per_size3 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.3, 1.4,1.5,2])
  acc_size3 = 1 - np.array([0.96,0.81,0.74, 0.69, 0.42, 0.33,0.13,0.1, 0.09, 0.09,0.05, 0.03,0.02,0.01])
  acc_size3 = acc_size3 * 100

  per_size4 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size4 = 1 - np.array([0.94, 0.9, 0.85, 0.37, 0.23, 0.26, 0.21, 0.08, 0.06, 0.02])
  acc_size4 = acc_size4 * 100

  per_size5 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size5 = 1 - np.array([0.95, 0.74, 0.41, 0.27, 0.16, 0.15, 0.11, 0.09, 0.06, 0.03])
  acc_size5 = acc_size5 * 100

  per_size6 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size6 = 1 - np.array([0.95, 0.59, 0.31, 0.23, 0.17, 0.13, 0.10, 0.04, 0.02, 0.02])
  acc_size6 = acc_size6 * 100

  per_size7 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size7 = 1 - np.array([0.83, 0.53, 0.3, 0.21, 0.12, 0.06, 0.03, 0.02, 0.02, 0.02])
  acc_size7 = acc_size7 * 100

  per_size8 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size8 = 1 - np.array([0.84, 0.52, 0.24, 0.21, 0.14, 0.09, 0.08, 0.05, 0.03, 0.01])
  acc_size8 = acc_size8 * 100

  per_size9 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size9 = 1 - np.array([0.84, 0.63, 0.33, 0.17, 0.13, 0.08, 0.05, 0.01,0.01,0.01])
  acc_size9 = acc_size9 * 100

  per_size10 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size10 = 1 - np.array([0.81, 0.73, 0.29, 0.13, 0.11, 0.06, 0.02, 0.02, 0.02, 0.02])
  acc_size10 = acc_size10 * 100

  for index, data in enumerate([
    [
     [per_size1, acc_size1],
     [per_size2, acc_size2],
     [per_size3, acc_size3],
     [per_size4, acc_size4],
     [per_size5, acc_size5]
     ],
    [
      [per_size6, acc_size6],
      [per_size7, acc_size7],
      [per_size8, acc_size8],
      [per_size9, acc_size9],
      [per_size10, acc_size10]
    ]
  ]):

    fig = plt.figure(figsize=(20, 4))
    pdf = PdfPages('mama_per_size_'+str(index)+'.pdf')

    title = ['Trigger Size ' + str(index*5 + 1)+'%', 'Trigger Size ' + str(index*5 + 2)+'%' , 'Trigger Size ' + str(index*5 + 3)+'%' ,'Trigger Size ' + str(index*5 + 4)+'%','Trigger Size ' + str(index*5 + 5)+'%']
    for i in range(5):
      ax1 = fig.add_subplot(1,5,i+1)

      plt.ylim(0, 100)
      plt.xticks(fontsize=12)
      plt.yticks(fontsize=16)
      plt.xlabel('% of poison data in training set', fontsize=16)
      plt.ylabel('Evasion Rate', fontsize=16)

      print(min(data[i][0]), max(data[i][0]))
      plt.xlim(min(data[i][0]), max(data[i][0]))
      print(data[i][0].shape, data[i][1].shape)
      ax1.plot(data[i][0], data[i][1], 'o-.', label='3-NN')

      font = {'family': 'Times New Roman',
              'color': 'black',
              'weight': 'normal',
              'size': 21,
              }
      # plt.xlabel(x_label[i], font)
      plt.title(title[i], font)
    # plt.legend(loc='upper center', bbox_to_anchor=(-1.5, 3), fontsize=20, ncol=4)
    plt.subplots_adjust(left=0.05, bottom=0.2, right=0.99, top=0.90, wspace = 0.35, hspace = 0.25)
    pdf.savefig()
    plt.close()
    pdf.close()
    # plt.show()
# mama_per_size()

def apiminer_per_size():
  per_size50 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size50 = 1 - np.array([0.63,0.52,0.42,0.37,0.32,0.3,0.29,0.27,0.26,0.25,0.23])
  acc_size50 = acc_size50 * 100

  per_size40 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size40 = 1 - np.array([0.68, 0.59, 0.49,0.43, 0.37,0.35,0.34,0.32,0.31,0.29,0.28])
  acc_size40 = acc_size40 * 100

  per_size30 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size30 = 1 - np.array([0.78,0.63,0.55,0.48,0.41,0.4,0.38,0.36,0.35,0.33,0.31])
  acc_size30 = acc_size30 * 100

  per_size20 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size20 = 1 - np.array([0.83,0.69,0.63,0.59,0.51,0.5,0.47,0.45,0.43,0.40,0.38])
  acc_size20 = acc_size20 * 100

  per_size10 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size10 = 1 - np.array([0.89,0.78,0.74,0.71,0.65,0.64,0.6,0.58,0.56,0.54,0.5])
  acc_size10 = acc_size10 * 100

  per_size60 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size60 = 1 - np.array([0.58, 0.47, 0.38, 0.34, 0.29, 0.28, 0.27, 0.25, 0.24, 0.23, 0.21])
  acc_size60 = acc_size60 * 100

  per_size70 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size70 = 1 - np.array([0.55, 0.43, 0.36, 0.31, 0.26, 0.24, 0.23, 0.22, 0.21, 0.19, 0.18])
  acc_size70 = acc_size70 * 100

  per_size80 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size80 = 1 - np.array([0.49, 0.38, 0.32, 0.27, 0.23, 0.21, 0.20, 0.19, 0.19, 0.17, 0.16])
  acc_size80 = acc_size80 * 100

  per_size90 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size90 = 1 - np.array([0.44, 0.36, 0.31, 0.26, 0.20, 0.20, 0.19, 0.18, 0.17, 0.16, 0.15])
  acc_size90 = acc_size90 * 100

  per_size100 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size100 = 1 - np.array([0.42, 0.33, 0.28, 0.23, 0.19, 0.18, 0.17, 0.16, 0.16, 0.15, 0.14])
  acc_size100 = acc_size100 * 100


  for index, data in enumerate([
    [
     [per_size10, acc_size10],
     [per_size20, acc_size20],
     [per_size30, acc_size30],
     [per_size40, acc_size40],
     [per_size50, acc_size50]
    ],
    [
      [per_size60, acc_size60],
      [per_size70, acc_size70],
      [per_size80, acc_size80],
      [per_size90, acc_size90],
      [per_size100, acc_size100]
    ]
  ]):

    fig = plt.figure(figsize=(20, 4))
    pdf = PdfPages('apiminer_per_size_'+str(index)+'.pdf')
    # title = ['Trigger Size 10', 'Trigger Size 20', 'Trigger Size 30', 'Trigger size 40', 'Trigger size 50']
    title = ['Trigger Size %.4f%s' % (((index*50 + 10)/991*100), '%') , 'Trigger Size %.4f%s' % (((index*50 + 20)/991*100), '%') , 'Trigger Size %.4f%s' % (((index*50 + 30)/991*100), '%'), 'Trigger Size %.4f%s' % (((index*50 + 40)/991*100), '%'),'Trigger Size %.4f%s' % (((index * 50 + 50)/991*100), '%')]
    for i in range(5):
      ax1 = fig.add_subplot(1,5,i+1)

      plt.ylim(0, 100)
      plt.xticks(fontsize=12)
      plt.yticks(fontsize=16)
      plt.xlabel('% of poison data in training set', fontsize=16)
      plt.ylabel('Evasion Rate', fontsize=16)

      print(min(data[i][0]), max(data[i][0]))
      plt.xlim(min(data[i][0]), max(data[i][0]))
      print(data[i][0].shape, data[i][1].shape)
      ax1.plot(data[i][0], data[i][1], 'o-.', label='3-NN')

      font = {'family': 'Times New Roman',
              'color': 'black',
              'weight': 'normal',
              'size': 21,
              }
      # plt.xlabel(x_label[i], font)
      plt.title(title[i], font)
    # plt.legend(loc='upper center', bbox_to_anchor=(-1.5, 3), fontsize=20, ncol=4)
    plt.subplots_adjust(left=0.05, bottom=0.2, right=0.99, top=0.90, wspace = 0.35, hspace = 0.25)
    pdf.savefig()
    plt.close()
    pdf.close()
    # plt.show()
# apiminer_per_size()

def droidcat_per_size():
  per_group1 = np.array([0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1,1.5,2])
  acc_group1 = 1 - np.array([407,381, 334,231,229,134,96,93,77,46,20,9])/673
  acc_group1 = acc_group1 * 100

  per_group2 = np.array([0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1,1.5,2])
  acc_group2 = 1 - np.array([290,140,67,51,26,19,18,12,10,10,1,1])/673
  acc_group2 = acc_group2 * 100

  FSET_YYY = [1, 2, 3, 10, 13, 16, 19, 37, 39, 41, 53, 55, 57, 58, 59, 60, 61, 63, 73, 74, 75, 76, 78, 80, 81, 82, 83,
              84, 93, 94, 95, 96, 105, 106, 117, 118, 11, 14, 22, 24, 30, 35, 38, 40, 43, 44, 54, 56, 62, 64, 65, 67,
              86, 88, 99, 100, 101, 102, 103, 104, 107, 108, 12, 15, 23, 28, 32, 34, 36, 42]
  print('===============', len(FSET_YYY))
  for index, data in enumerate([
    [
     [per_group1, acc_group1],
     [per_group2, acc_group2],
     [per_group2, per_group2],
     [per_group2, per_group2],
     [per_group2, per_group2]
    ]
  ]):

    fig = plt.figure(figsize=(9, 4))
    pdf = PdfPages('droidcat_per_size_'+str(index)+'.pdf')
    # FSET_YYY = [1, 2, 3, 10, 13, 16, 19, 37, 39, 41, 53, 55, 57, 58, 59, 60, 61, 63, 73, 74, 75, 76, 78, 80, 81, 82, 83,
    #             84, 93, 94, 95, 96, 105, 106, 117, 118, 11, 14, 22, 24, 30, 35, 38, 40, 43, 44, 54, 56, 62, 64, 65, 67,
    #             86, 88, 99, 100, 101, 102, 103, 104, 107, 108, 12, 15, 23, 28, 32, 34, 36, 42]
    # print(len(FSET_YYY))
    # title = ['Trigger Size 3', 'Trigger Size 6', 'Trigger size 30', 'Trigger size 40', 'Trigger size 50']
    title = ['Trigger Size 4.2857%', 'Trigger Size 8.5714%', 'Trigger size 30', 'Trigger size 40', 'Trigger size 50']
    for i in range(5):
      ax1 = fig.add_subplot(1, 5, i+1)

      plt.ylim(0, 100)
      plt.xticks(fontsize=12)
      plt.yticks(fontsize=16)
      plt.xlabel('% of poison data in training set', fontsize=16)
      plt.ylabel('Evasion Rate', fontsize=16)

      print(min(data[i][0]), max(data[i][0]))
      plt.xlim(min(data[i][0]), max(data[i][0]))
      print(data[i][0].shape, data[i][1].shape)
      ax1.plot(data[i][0], data[i][1], 'o-.', label='3-NN')

      font = {'family': 'Times New Roman',
              'color': 'black',
              'weight': 'normal',
              'size': 21,
              }
      # plt.xlabel(x_label[i], font)
      plt.title(title[i], font)
    # plt.legend(loc='upper center', bbox_to_anchor=(-1.5, 3), fontsize=20, ncol=4)
    plt.subplots_adjust(left=0.1, bottom=0.2, right=2.5, top=0.90, wspace = 0.5, hspace = 0.25)
    pdf.savefig()
    plt.close()
    pdf.close()
    # plt.show()
# droidcat_per_size()

# ==========================================
# ||
# || title: poisoning rate, y:evasion rate, x:trigger size
# ||
# ==========================================

# transform
def transform(title_val, x_val, ori_data):
  y_val = []
  dics = []
  for tem in ori_data:
    dic={}
    for i2, tem2 in enumerate(title_val):
      if tem2 in tem[0]:
        dic[tem2] = tem[1][i2]
      else:
        print(np.where(tem[0] < tem2))
        exit(2)
    dics.append(dic)

  for i in title_val:
    tem_y=[]
    for j in range(10):
      tem_y.append(dics[j][i])
    y_val.append(tem_y)
  data = [
  [
   [x_val, y_val[0]],
   [x_val, y_val[1]],
   [x_val, y_val[2]],
   [x_val, y_val[3]],
   [x_val, y_val[4]]
   ],
  [
    [x_val, y_val[5]],
    [x_val, y_val[6]],
    [x_val, y_val[7]],
    [x_val, y_val[8]],
    [x_val, y_val[9]]
  ]
]
  return data

def transform11(poison, size, ori_data):
  y_val = []
  dics = []
  for tem in ori_data:
    dic={}
    for i2, tem2 in enumerate(poison):
      if tem2 in tem[0]:
        dic[tem2] = tem[1][i2+1]
      else:
        print(tem2)
        print(tem[0])
        print('!!!!!!!!!')
        exit(2)
    dics.append(dic)

  for i in poison:
    tem_y=[]
    for j in range(10):
      tem_y.append(dics[j][i])
    y_val.append(tem_y)
  data = [
  [
   [size, y_val[0]],
   [size, y_val[1]],
   [size, y_val[2]],
   [size, y_val[3]],
   [size, y_val[4]]
   ],
  [
    [size, y_val[5]],
    [size, y_val[6]],
    [size, y_val[7]],
    [size, y_val[8]],
    [size, y_val[9]]
  ]
]
  return data


def drebin_per_size():
  per_size1 = np.array([0.1,0.2,0.3, 0.4, 0.5, 0.6,0.7, 0.8, 0.9,1.0])
  acc_size1 = 1 - np.array([0.34, 0.13, 0.09, 0.06, 0.06, 0.05, 0.04,0.03,0.03,0.03])
  acc_size1 = acc_size1 * 100

  per_size2 = np.array([0.1,0.2, 0.3,0.4,1.0])
  acc_size2 = 1 - np.array([0.14,0.06,0.06,0.02,0.02])
  acc_size2 = acc_size2 * 100

  per_size3 = np.array([0.1,0.2,0.3,1.0])
  acc_size3 = 1 - np.array([0.12,0.06,0.02,0.02])
  acc_size3 = acc_size3 * 100

  per_size4 = np.array([0.1, 0.2, 0.3,1.0])
  acc_size4 = 1 - np.array([0.11, 0.06, 0.01, 0.01])
  acc_size4 = acc_size4 * 100

  per_size5 = per_size4
  acc_size5 = acc_size4

  per_size6 = np.array([0.1, 0.2, 0.3, 1.0])
  acc_size6 = 1 - np.array([0.03, 0.03, 0.02, 0.02])
  acc_size6 = acc_size6 * 100

  per_size7 = per_size6
  acc_size7 = acc_size6

  per_size8 = per_size6
  acc_size8 = acc_size6

  per_size9 = per_size6
  acc_size9 = acc_size6

  per_size10 = per_size6
  acc_size10 = acc_size6

  size = np.array(range(1, 11))
  print(size / 45475)
  size = np.around(size / 45475 * 10e4, decimals=2)
  # size = size / 45475
  print(size)
  poison = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
  acc_1 = 1 - np.array([0.34,0.14,0.12,0.11,0.11,0.03,0.03,0.03,0.03,0.03])
  acc_1 = acc_1 *100
  acc_2 = 1 - np.array([0.13, 0.06, 0.06, 0.06, 0.06, 0.03, 0.03, 0.03, 0.03, 0.03])
  acc_2 = acc_2 *100
  acc_3 = 1 - np.array([0.09, 0.06, 0.02, 0.01, 0.01, 0.02, 0.02, 0.02, 0.02, 0.02])
  acc_3 = acc_3 *100
  acc_4 = 1 - np.array([0.06, 0.02, 0.02, 0.01, 0.01, 0.02, 0.02, 0.02, 0.02, 0.02])
  acc_4 = acc_4 *100
  acc_5 = 1 - np.array([0.06, 0.02, 0.02, 0.01, 0.01, 0.02, 0.02, 0.02, 0.02, 0.02])
  acc_5 = acc_5 *100

  for index, data in enumerate([
    [
     [size, acc_1],
     [size, acc_2],
     [size, acc_3],
     [size, acc_4],
     [size, acc_5]
    ]
  ]):

    fig = plt.figure(figsize=(20, 4))
    pdf = PdfPages('drebin_per_size_'+str(index)+'.pdf')

    # title = ['Trigger Size 1', 'Trigger Size 2', 'Trigger Size 3', 'Trigger Size 4&5', 'Trigger Size 6-10']
    # title = ['Trigger Size 0.0690%', 'Trigger Size 0.1379%', 'Trigger Size 0.2069%', 'Trigger Size \n0.2759% & 0.3448%', 'Trigger Size \n0.4138%-0.6897%']
    for i in range(5):
      ax1 = fig.add_subplot(1,5,i+1)
      title = str(poison[i])+'% Poisoning Data'
      plt.ylim(0, 100)
      plt.xticks(fontsize=12)
      plt.yticks(fontsize=16)
      plt.xlabel('% of Trigger Size (×10e-4)', fontsize=16)
      plt.ylabel('Evasion Rate', fontsize=16)

      print(min(data[i][0]), max(data[i][0]))
      plt.xlim(min(data[i][0]), max(data[i][0]))
      print(data[i][0].shape, data[i][1].shape)
      ax1.plot(data[i][0], data[i][1], 'o-.', label='3-NN')
      print(data[i][1])
      font = {'family': 'Times New Roman',
              'color': 'black',
              'weight': 'normal',
              'size': 21,
              }
      # plt.xlabel(x_label[i], font)
      plt.title(title, font)
    # plt.legend(loc='upper center', bbox_to_anchor=(-1.5, 3), fontsize=20, ncol=4)
    plt.subplots_adjust(left=0.05, bottom=0.2, right=0.99, top=0.84, wspace = 0.35, hspace = 0.25)
    pdf.savefig()
    plt.close()
    pdf.close()
    # plt.show()
# drebin_per_size()

def mama_per_size():
  per_size1 = np.array([0.1,  0.2,  0.3,  0.4,  0.5,  0.6,  0.7,  0.8,  0.9,  1.0,  1.1,  1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 2,    3,    4,   5,   7,   8,    9,    10])
  acc_size1 = 1 - np.array([0.96, 0.96, 0.96, 0.95, 0.93, 0.91, 0.91, 0.72, 0.65, 0.52, 0.41, 0.36, 0.34, 0.26, 0.26, 0.26, 0.25, 0.24, 0.23, 0.1, 0.1, 0.1, 0.06, 0.06, 0.01])
  acc_size1 = acc_size1 * 100

  per_size2 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8])
  acc_size2 = 1 - np.array([0.95, 0.96, 0.94, 0.9, 0.79, 0.45, 0.27, 0.26, 0.21, 0.21, 0.15, 0.15, 0.13, 0.13, 0.13, 0.13, 0.06, 0.03])
  acc_size2 = acc_size2 * 100

  per_size3 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.3, 1.4,1.5,2])
  acc_size3 = 1 - np.array([0.96,0.81,0.74, 0.69, 0.42, 0.33,0.13,0.1, 0.09, 0.09,0.05, 0.03,0.02,0.01])
  acc_size3 = acc_size3 * 100

  per_size4 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size4 = 1 - np.array([0.94, 0.9, 0.85, 0.37, 0.23, 0.26, 0.21, 0.08, 0.06, 0.02])
  acc_size4 = acc_size4 * 100

  per_size5 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size5 = 1 - np.array([0.95, 0.74, 0.41, 0.27, 0.16, 0.15, 0.11, 0.09, 0.06, 0.03])
  acc_size5 = acc_size5 * 100

  per_size6 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size6 = 1 - np.array([0.95, 0.59, 0.31, 0.23, 0.17, 0.13, 0.10, 0.04, 0.02, 0.02])
  acc_size6 = acc_size6 * 100

  per_size7 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size7 = 1 - np.array([0.83, 0.53, 0.3, 0.21, 0.12, 0.06, 0.03, 0.02, 0.02, 0.02])
  acc_size7 = acc_size7 * 100

  per_size8 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size8 = 1 - np.array([0.84, 0.52, 0.24, 0.21, 0.14, 0.09, 0.08, 0.05, 0.03, 0.01])
  acc_size8 = acc_size8 * 100

  per_size9 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size9 = 1 - np.array([0.84, 0.63, 0.33, 0.17, 0.13, 0.08, 0.05, 0.01,0.01,0.01])
  acc_size9 = acc_size9 * 100

  per_size10 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size10 = 1 - np.array([0.81, 0.73, 0.29, 0.13, 0.11, 0.06, 0.02, 0.02, 0.02, 0.02])
  acc_size10 = acc_size10 * 100

  ori_data = [
    [per_size1, acc_size1],
    [per_size2, acc_size2],
    [per_size3, acc_size3],
    [per_size4, acc_size4],
    [per_size5, acc_size5],
    [per_size6, acc_size6],
    [per_size7, acc_size7],
    [per_size8, acc_size8],
    [per_size9, acc_size9],
    [per_size10, acc_size10]
  ]
  title_val = per_size10
  x_val = np.array(range(1,11))
  alldata = transform(title_val, x_val, ori_data)

  for index, data in enumerate(alldata):

    fig = plt.figure(figsize=(20, 4))
    pdf = PdfPages('mama_per_size_'+str(index)+'.pdf')


    for i in range(5):
      total_i = index*5+i
      title = str(title_val[total_i]) + '% Poisoning Data'
      ax1 = fig.add_subplot(1,5,i+1)
      plt.ylim(0, 100)
      plt.xticks(fontsize=12)
      plt.yticks(fontsize=16)
      plt.xlabel('% of Trigger Size', fontsize=16)
      plt.ylabel('Evasion Rate', fontsize=16)

      print(min(data[i][0]), max(data[i][0]))
      plt.xlim(min(data[i][0]), max(data[i][0]))
      # print(data[i][0].shape, data[i][1].shape)
      ax1.plot(data[i][0], data[i][1], 'o-.', label='3-NN')

      font = {'family': 'Times New Roman',
              'color': 'black',
              'weight': 'normal',
              'size': 21,
              }
      # plt.xlabel(x_label[i], font)
      plt.title(title, font)
    # plt.legend(loc='upper center', bbox_to_anchor=(-1.5, 3), fontsize=20, ncol=4)
    plt.subplots_adjust(left=0.05, bottom=0.2, right=0.99, top=0.90, wspace = 0.35, hspace = 0.25)
    pdf.savefig()
    plt.close()
    pdf.close()
    # plt.show()
# mama_per_size()

def apiminer_per_size():
  per_size50 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size50 = 1 - np.array([0.63,0.52,0.42,0.37,0.32,0.3,0.29,0.27,0.26,0.25,0.23])
  acc_size50 = acc_size50 * 100

  per_size40 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size40 = 1 - np.array([0.68, 0.59, 0.49,0.43, 0.37,0.35,0.34,0.32,0.31,0.29,0.28])
  acc_size40 = acc_size40 * 100

  per_size30 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size30 = 1 - np.array([0.78,0.63,0.55,0.48,0.41,0.4,0.38,0.36,0.35,0.33,0.31])
  acc_size30 = acc_size30 * 100

  per_size20 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size20 = 1 - np.array([0.83,0.69,0.63,0.59,0.51,0.5,0.47,0.45,0.43,0.40,0.38])
  acc_size20 = acc_size20 * 100

  per_size10 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size10 = 1 - np.array([0.89,0.78,0.74,0.71,0.65,0.64,0.6,0.58,0.56,0.54,0.5])
  acc_size10 = acc_size10 * 100

  per_size60 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size60 = 1 - np.array([0.58, 0.47, 0.38, 0.34, 0.29, 0.28, 0.27, 0.25, 0.24, 0.23, 0.21])
  acc_size60 = acc_size60 * 100

  per_size70 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size70 = 1 - np.array([0.55, 0.43, 0.36, 0.31, 0.26, 0.24, 0.23, 0.22, 0.21, 0.19, 0.18])
  acc_size70 = acc_size70 * 100

  per_size80 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size80 = 1 - np.array([0.49, 0.38, 0.32, 0.27, 0.23, 0.21, 0.20, 0.19, 0.19, 0.17, 0.16])
  acc_size80 = acc_size80 * 100

  per_size90 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size90 = 1 - np.array([0.44, 0.36, 0.31, 0.26, 0.20, 0.20, 0.19, 0.18, 0.17, 0.16, 0.15])
  acc_size90 = acc_size90 * 100

  per_size100 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size100 = 1 - np.array([0.42, 0.33, 0.28, 0.23, 0.19, 0.18, 0.17, 0.16, 0.16, 0.15, 0.14])
  acc_size100 = acc_size100 * 100

  ori_data = [
    [per_size10, acc_size10],
    [per_size20, acc_size20],
    [per_size30, acc_size30],
    [per_size40, acc_size40],
    [per_size50, acc_size50],
    [per_size60, acc_size60],
    [per_size70, acc_size70],
    [per_size80, acc_size80],
    [per_size90, acc_size90],
    [per_size100, acc_size100]
  ]

  poison = np.array([0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  size = np.round(np.array(range(1, 11))*10/991*100, decimals=2)
  print(size)
  alldata = transform11(poison, size, ori_data)

  for index, data in enumerate(alldata):

    fig = plt.figure(figsize=(20, 4))
    pdf = PdfPages('apiminer_per_size_'+str(index)+'.pdf')
    # title = ['Trigger Size 10', 'Trigger Size 20', 'Trigger Size 30', 'Trigger size 40', 'Trigger size 50']
    # title = ['Trigger Size %.4f%s' % (((index*50 + 10)/991*100), '%') , 'Trigger Size %.4f%s' % (((index*50 + 20)/991*100), '%') , 'Trigger Size %.4f%s' % (((index*50 + 30)/991*100), '%'), 'Trigger Size %.4f%s' % (((index*50 + 40)/991*100), '%'),'Trigger Size %.4f%s' % (((index * 50 + 50)/991*100), '%')]
    for i in range(5):
      ax1 = fig.add_subplot(1,5,i+1)
      title = str(poison[index*5+i])+'% Poisoning Data'
      plt.ylim(0, 100)
      plt.xticks(fontsize=12)
      plt.yticks(fontsize=16)
      plt.xlabel('% of Trigger Size', fontsize=16)
      plt.ylabel('Evasion Rate', fontsize=16)

      print(min(data[i][0]), max(data[i][0]))
      plt.xlim(min(data[i][0]), max(data[i][0]))
      # print(data[i][0].shape, data[i][1].shape)
      ax1.plot(data[i][0], data[i][1], 'o-.', label='3-NN')

      font = {'family': 'Times New Roman',
              'color': 'black',
              'weight': 'normal',
              'size': 21,
              }
      # plt.xlabel(x_label[i], font)
      plt.title(title, font)
    # plt.legend(loc='upper center', bbox_to_anchor=(-1.5, 3), fontsize=20, ncol=4)
    plt.subplots_adjust(left=0.05, bottom=0.2, right=0.99, top=0.90, wspace = 0.35, hspace = 0.25)
    pdf.savefig()
    plt.close()
    pdf.close()
    # plt.show()
# apiminer_per_size()

def droidcat_per_size():
  per_group1 = np.array([0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1,1.5,2])
  acc_group1 = 1 - np.array([407,381, 334,231,229,134,96,93,77,46,20,9])/673
  acc_group1 = acc_group1 * 100

  per_group2 = np.array([0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1,1.5,2])
  acc_group2 = 1 - np.array([290,140,67,51,26,19,18,12,10,10,1,1])/673
  acc_group2 = acc_group2 * 100

  poison = np.array([0.1, 0.3, 0.5, 0.7, 2])
  poison_index = [np.where(per_group1==i)[0][0] for i in poison]
  print(poison_index)
  size = np.array([3/70, 6/70])
  iter_data = []
  print('##################')
  for i in poison_index:
    iter_data.append([size*100, np.array([acc_group1[i],acc_group2[i]])])
  iter_data = np.array([iter_data])
  print(iter_data.shape)
  FSET_YYY = [1, 2, 3, 10, 13, 16, 19, 37, 39, 41, 53, 55, 57, 58, 59, 60, 61, 63, 73, 74, 75, 76, 78, 80, 81, 82, 83,
              84, 93, 94, 95, 96, 105, 106, 117, 118, 11, 14, 22, 24, 30, 35, 38, 40, 43, 44, 54, 56, 62, 64, 65, 67,
              86, 88, 99, 100, 101, 102, 103, 104, 107, 108, 12, 15, 23, 28, 32, 34, 36, 42]
  print('===============', len(FSET_YYY))

  for index, data in enumerate(iter_data):
    fig = plt.figure(figsize=(20, 4))
    pdf = PdfPages('droidcat_per_size_'+str(index)+'.pdf')
    # FSET_YYY = [1, 2, 3, 10, 13, 16, 19, 37, 39, 41, 53, 55, 57, 58, 59, 60, 61, 63, 73, 74, 75, 76, 78, 80, 81, 82, 83,
    #             84, 93, 94, 95, 96, 105, 106, 117, 118, 11, 14, 22, 24, 30, 35, 38, 40, 43, 44, 54, 56, 62, 64, 65, 67,
    #             86, 88, 99, 100, 101, 102, 103, 104, 107, 108, 12, 15, 23, 28, 32, 34, 36, 42]
    # print(len(FSET_YYY))
    # title = ['Trigger Size 3', 'Trigger Size 6', 'Trigger size 30', 'Trigger size 40', 'Trigger size 50']
    # title = ['Trigger Size 4.2857%', 'Trigger Size 8.5714%', 'Trigger size 30', 'Trigger size 40', 'Trigger size 50']
    for i in range(poison.shape[0]):
      ax1 = fig.add_subplot(1, poison.shape[0], i+1)
      title = str(poison[i])+'% Poisoning Data'
      plt.ylim(0, 100)
      plt.xticks(fontsize=12)
      plt.yticks(fontsize=16)
      plt.xlabel('% of Trigger Size', fontsize=16)
      plt.ylabel('Evasion Rate', fontsize=16)
      print(data[i])
      print(min(data[i][0]), max(data[i][0]))
      plt.xlim(min(data[i][0]), max(data[i][0]))
      # print(data[i][0].shape, data[i][1].shape)
      ax1.plot(data[i][0], data[i][1], 'o-.', label='3-NN')

      font = {'family': 'Times New Roman',
              'color': 'black',
              'weight': 'normal',
              'size': 21,
              }
      # plt.xlabel(x_label[i], font)
      plt.title(title, font)
    # plt.legend(loc='upper center', bbox_to_anchor=(-1.5, 3), fontsize=20, ncol=4)
    plt.subplots_adjust(left=0.05, bottom=0.2, right=0.99, top=0.90, wspace = 0.35, hspace = 0.25)
    pdf.savefig()
    plt.close()
    pdf.close()
    # plt.show()
# droidcat_per_size()

# ==========================================
# ||
# || title: poisoning rate, y:evasion rate, x:trigger size
# ||
# ==========================================
def drebin_per_size_onegroup():

  # ================== drebin ==================
  per_size1 = np.array([0.1,0.2,0.3, 0.4, 0.5, 0.6,0.7, 0.8, 0.9,1.0])
  acc_size1 = 1 - np.array([0.34, 0.13, 0.09, 0.06, 0.06, 0.05, 0.04,0.03,0.03,0.03])
  acc_size1 = acc_size1 * 100

  per_size2 = np.array([0.1,0.2, 0.3,0.4,1.0])
  acc_size2 = 1 - np.array([0.14,0.06,0.06,0.02,0.02])
  acc_size2 = acc_size2 * 100

  per_size3 = np.array([0.1,0.2,0.3,1.0])
  acc_size3 = 1 - np.array([0.12,0.06,0.02,0.02])
  acc_size3 = acc_size3 * 100

  per_size4 = np.array([0.1, 0.2, 0.3,1.0])
  acc_size4 = 1 - np.array([0.11, 0.06, 0.01, 0.01])
  acc_size4 = acc_size4 * 100

  per_size5 = per_size4
  acc_size5 = acc_size4

  per_size6 = np.array([0.1, 0.2, 0.3, 1.0])
  acc_size6 = 1 - np.array([0.03, 0.03, 0.02, 0.02])
  acc_size6 = acc_size6 * 100

  per_size7 = per_size6
  acc_size7 = acc_size6

  per_size8 = per_size6
  acc_size8 = acc_size6

  per_size9 = per_size6
  acc_size9 = acc_size6

  per_size10 = per_size6
  acc_size10 = acc_size6

  size = np.array(range(1, 11))
  print(size / 45475)
  size = np.around(size / 45475 * 10e4, decimals=2)
  # size = size / 45475
  print(size)
  poison = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
  acc_1 = 1 - np.array([0.34,0.14,0.12,0.11,0.11,0.03,0.03,0.03,0.03,0.03])
  acc_1 = acc_1 *100
  acc_2 = 1 - np.array([0.13, 0.06, 0.06, 0.06, 0.06, 0.03, 0.03, 0.03, 0.03, 0.03])
  acc_2 = acc_2 *100
  acc_3 = 1 - np.array([0.09, 0.06, 0.02, 0.01, 0.01, 0.02, 0.02, 0.02, 0.02, 0.02])
  acc_3 = acc_3 *100
  acc_4 = 1 - np.array([0.06, 0.02, 0.02, 0.01, 0.01, 0.02, 0.02, 0.02, 0.02, 0.02])
  acc_4 = acc_4 *100
  acc_5 = 1 - np.array([0.06, 0.02, 0.02, 0.01, 0.01, 0.02, 0.02, 0.02, 0.02, 0.02])
  acc_5 = acc_5 *100

  for index, data in enumerate([
    [
     [size, acc_1],
     [size, acc_2],
     [size, acc_3],
     [size, acc_4],
     [size, acc_5]
    ]
  ]):

    # fig = plt.figure(figsize=(20, 20))
    pdf = PdfPages('drebin_per_size_'+str(index)+'_onegroup.pdf')

    # title = ['Trigger Size 1', 'Trigger Size 2', 'Trigger Size 3', 'Trigger Size 4&5', 'Trigger Size 6-10']
    # title = ['Trigger Size 0.0690%', 'Trigger Size 0.1379%', 'Trigger Size 0.2069%', 'Trigger Size \n0.2759% & 0.3448%', 'Trigger Size \n0.4138%-0.6897%']
    # for i in range(5):

    # ax1 = fig.add_subplot(2,2,1)
    # title = str(poison[i])+'% Poisoning Data'
    title = '(a) Drebin'
    plt.ylim(0, 100)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=16)
    plt.xlabel('% of Trigger Size (×10e-4)', fontsize=16)
    plt.ylabel('Evasion Rate', fontsize=16)

    # print(min(data[i][0]), max(data[i][0]))
    plt.xlim(min(data[0][0]), max(data[0][0]))
    # print(data[i][0].shape, data[i][1].shape)
    plt.plot(data[0][0], data[0][1], 'o-.', label='0.1% poisoning data')
    plt.plot(data[1][0], data[1][1], '*:', label='0.2% poisoning data')
    plt.plot(data[2][0], data[2][1], 'h-', label='0.3% poisoning data')
    plt.plot(data[3][0], data[3][1], 's--', label='0.4% poisoning data')
    plt.plot(data[4][0], data[4][1], 'o:', label='0.5% poisoning data')
    # print(data[i][1])
    font = {'family': 'Times New Roman',
            'color': 'black',
            'weight': 'normal',
            'size': 21,
            }
    # plt.xlabel(x_label[i], font)
    plt.title(title, font)
    # plt.legend(loc='upper center', bbox_to_anchor=(-1.5, 3), fontsize=20, ncol=4)
    plt.legend(loc='lower right', fontsize=14, ncol=1)
    plt.subplots_adjust(left=0.15, bottom=0.2, right=0.99, top=0.84, wspace = 0.35, hspace = 0.25)
    # ================== drebin ==================

    pdf.savefig()
    plt.close()
    pdf.close()
    # plt.show()
# drebin_per_size_onegroup()

def mama_per_size_onegroup():
  per_size1 = np.array([0.1,  0.2,  0.3,  0.4,  0.5,  0.6,  0.7,  0.8,  0.9,  1.0,  1.1,  1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 2,    3,    4,   5,   7,   8,    9,    10])
  acc_size1 = 1 - np.array([0.96, 0.96, 0.96, 0.95, 0.93, 0.91, 0.91, 0.72, 0.65, 0.52, 0.41, 0.36, 0.34, 0.26, 0.26, 0.26, 0.25, 0.24, 0.23, 0.1, 0.1, 0.1, 0.06, 0.06, 0.01])
  acc_size1 = acc_size1 * 100

  per_size2 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8])
  acc_size2 = 1 - np.array([0.95, 0.96, 0.94, 0.9, 0.79, 0.45, 0.27, 0.26, 0.21, 0.21, 0.15, 0.15, 0.13, 0.13, 0.13, 0.13, 0.06, 0.03])
  acc_size2 = acc_size2 * 100

  per_size3 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.3, 1.4,1.5,2])
  acc_size3 = 1 - np.array([0.96,0.81,0.74, 0.69, 0.42, 0.33,0.13,0.1, 0.09, 0.09,0.05, 0.03,0.02,0.01])
  acc_size3 = acc_size3 * 100

  per_size4 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size4 = 1 - np.array([0.94, 0.9, 0.85, 0.37, 0.23, 0.26, 0.21, 0.08, 0.06, 0.02])
  acc_size4 = acc_size4 * 100

  per_size5 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size5 = 1 - np.array([0.95, 0.74, 0.41, 0.27, 0.16, 0.15, 0.11, 0.09, 0.06, 0.03])
  acc_size5 = acc_size5 * 100

  per_size6 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size6 = 1 - np.array([0.95, 0.59, 0.31, 0.23, 0.17, 0.13, 0.10, 0.04, 0.02, 0.02])
  acc_size6 = acc_size6 * 100

  per_size7 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size7 = 1 - np.array([0.83, 0.53, 0.3, 0.21, 0.12, 0.06, 0.03, 0.02, 0.02, 0.02])
  acc_size7 = acc_size7 * 100

  per_size8 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size8 = 1 - np.array([0.84, 0.52, 0.24, 0.21, 0.14, 0.09, 0.08, 0.05, 0.03, 0.01])
  acc_size8 = acc_size8 * 100

  per_size9 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size9 = 1 - np.array([0.84, 0.63, 0.33, 0.17, 0.13, 0.08, 0.05, 0.01,0.01,0.01])
  acc_size9 = acc_size9 * 100

  per_size10 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size10 = 1 - np.array([0.81, 0.73, 0.29, 0.13, 0.11, 0.06, 0.02, 0.02, 0.02, 0.02])
  acc_size10 = acc_size10 * 100

  ori_data = [
    [per_size1, acc_size1],
    [per_size2, acc_size2],
    [per_size3, acc_size3],
    [per_size4, acc_size4],
    [per_size5, acc_size5],
    [per_size6, acc_size6],
    [per_size7, acc_size7],
    [per_size8, acc_size8],
    [per_size9, acc_size9],
    [per_size10, acc_size10]
  ]
  title_val = per_size10
  x_val = np.array(range(1,11))
  alldata = transform(title_val, x_val, ori_data)

  new_data = []
  for index, data in enumerate(alldata):
    for i in range(5):
      # print('=============')
      # print(data[i][1])
      new_data.append([data[i][0], data[i][1]])
  # print('=============')
  # print(len(new_data))
  data = new_data
  # fig = plt.figure(figsize=(20, 4))
  pdf = PdfPages('mama_per_size_'+str(index)+'_onegroup.pdf')


  # for i in range(5):
  title = '(b) MaMaDroid'
  # title = str(title_val[total_i]) + '% Poisoning Data'
  # ax1 = fig.add_subplot(1,5,i+1)
  plt.ylim(0, 100)
  plt.xticks(fontsize=12)
  plt.yticks(fontsize=16)
  plt.xlabel('% of Trigger Size', fontsize=16)
  plt.ylabel('Evasion Rate', fontsize=16)

  # print(min(data[i][0]), max(data[i][0]))
  plt.xlim(min(data[6][0]), max(data[6][0]))
  # print(data[i][0].shape, data[i][1].shape)
  # plt.plot(data[i][0], data[i][1], 'o-.', label='3-NN')
  plt.plot(data[0][0], data[0][1], 'o-.', label='0.1% poisoning data')
  plt.plot(data[2][0], data[2][1], '*:', label='0.3% poisoning data')
  plt.plot(data[4][0], data[3][1], 'h-', label='0.5% poisoning data')
  # print(len(data[6][0]))
  # print(len(data[6][1]))
  plt.plot(data[6][0], data[6][1], 's--', label='0.7% poisoning data')
  plt.plot(data[8][0], data[8][1], 'o:', label='0.9% poisoning data')
  font = {'family': 'Times New Roman',
          'color': 'black',
          'weight': 'normal',
          'size': 21,
          }
  # plt.xlabel(x_label[i], font)
  plt.title(title, font)
  plt.legend(loc='lower right', fontsize=10, ncol=1)
  plt.subplots_adjust(left=0.15, bottom=0.2, right=0.97, top=0.84, wspace = 0.35, hspace = 0.25)
  pdf.savefig()
  plt.close()
  pdf.close()
  # plt.show()
# mama_per_size_onegroup()

def apiminer_per_size_onegroup():
  per_size50 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size50 = 1 - np.array([0.63,0.52,0.42,0.37,0.32,0.3,0.29,0.27,0.26,0.25,0.23])
  acc_size50 = acc_size50 * 100

  per_size40 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size40 = 1 - np.array([0.68, 0.59, 0.49,0.43, 0.37,0.35,0.34,0.32,0.31,0.29,0.28])
  acc_size40 = acc_size40 * 100

  per_size30 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size30 = 1 - np.array([0.78,0.63,0.55,0.48,0.41,0.4,0.38,0.36,0.35,0.33,0.31])
  acc_size30 = acc_size30 * 100

  per_size20 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size20 = 1 - np.array([0.83,0.69,0.63,0.59,0.51,0.5,0.47,0.45,0.43,0.40,0.38])
  acc_size20 = acc_size20 * 100

  per_size10 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size10 = 1 - np.array([0.89,0.78,0.74,0.71,0.65,0.64,0.6,0.58,0.56,0.54,0.5])
  acc_size10 = acc_size10 * 100

  per_size60 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size60 = 1 - np.array([0.58, 0.47, 0.38, 0.34, 0.29, 0.28, 0.27, 0.25, 0.24, 0.23, 0.21])
  acc_size60 = acc_size60 * 100

  per_size70 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size70 = 1 - np.array([0.55, 0.43, 0.36, 0.31, 0.26, 0.24, 0.23, 0.22, 0.21, 0.19, 0.18])
  acc_size70 = acc_size70 * 100

  per_size80 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size80 = 1 - np.array([0.49, 0.38, 0.32, 0.27, 0.23, 0.21, 0.20, 0.19, 0.19, 0.17, 0.16])
  acc_size80 = acc_size80 * 100

  per_size90 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size90 = 1 - np.array([0.44, 0.36, 0.31, 0.26, 0.20, 0.20, 0.19, 0.18, 0.17, 0.16, 0.15])
  acc_size90 = acc_size90 * 100

  per_size100 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size100 = 1 - np.array([0.42, 0.33, 0.28, 0.23, 0.19, 0.18, 0.17, 0.16, 0.16, 0.15, 0.14])
  acc_size100 = acc_size100 * 100

  ori_data = [
    [per_size10, acc_size10],
    [per_size20, acc_size20],
    [per_size30, acc_size30],
    [per_size40, acc_size40],
    [per_size50, acc_size50],
    [per_size60, acc_size60],
    [per_size70, acc_size70],
    [per_size80, acc_size80],
    [per_size90, acc_size90],
    [per_size100, acc_size100]
  ]

  poison = np.array([0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  size = np.round(np.array(range(1, 11))*10/991*100, decimals=2)
  print(size)
  alldata = transform11(poison, size, ori_data)

  new_data = []
  for index, data in enumerate(alldata):
    for i in range(5):
      # print('=============')
      # print(data[i][1])
      new_data.append([data[i][0], data[i][1]])
  # print('=============')
  # print(len(new_data))
  data = new_data

  # for index, data in enumerate(alldata):

  # fig = plt.figure(figsize=(20, 4))
  pdf = PdfPages('apiminer_per_size_'+str(index)+'_onegroup.pdf')
  # title = ['Trigger Size 10', 'Trigger Size 20', 'Trigger Size 30', 'Trigger size 40', 'Trigger size 50']
  # title = ['Trigger Size %.4f%s' % (((index*50 + 10)/991*100), '%') , 'Trigger Size %.4f%s' % (((index*50 + 20)/991*100), '%') , 'Trigger Size %.4f%s' % (((index*50 + 30)/991*100), '%'), 'Trigger Size %.4f%s' % (((index*50 + 40)/991*100), '%'),'Trigger Size %.4f%s' % (((index * 50 + 50)/991*100), '%')]
  # for i in range(5):
  # ax1 = fig.add_subplot(1,5,i+1)
  # title = str(poison[index*5+i])+'% Poisoning Data'
  title = '(c) DroidAPIMiner'
  plt.ylim(0, 100)
  plt.xticks(fontsize=12)
  plt.yticks(fontsize=16)
  plt.xlabel('% of Trigger Size', fontsize=16)
  plt.ylabel('Evasion Rate', fontsize=16)

  # print(min(data[i][0]), max(data[i][0]))
  plt.xlim(min(data[0][0]), max(data[0][0]))
  # print(data[i][0].shape, data[i][1].shape)
  plt.plot(data[0][0], data[0][1], 'o-.', label='0.5% poisoning data')
  plt.plot(data[2][0], data[2][1], '*:', label='1.5% poisoning data')
  plt.plot(data[4][0], data[3][1], 'h-', label='2.5% poisoning data')
  # print(len(data[6][0]))
  # print(len(data[6][1]))
  plt.plot(data[6][0], data[6][1], 's--', label='3.5% poisoning data')
  plt.plot(data[8][0], data[8][1], 'o:', label='4.5% poisoning data')

  font = {'family': 'Times New Roman',
          'color': 'black',
          'weight': 'normal',
          'size': 21,
          }
  # plt.xlabel(x_label[i], font)
  plt.title(title, font)
  plt.legend(loc='lower right', fontsize=10, ncol=1)
  plt.subplots_adjust(left=0.15, bottom=0.2, right=0.99, top=0.90, wspace = 0.35, hspace = 0.25)
  pdf.savefig()
  plt.close()
  pdf.close()
  # plt.show()
# apiminer_per_size_onegroup()

def droidcat_per_size_onegroup():
  per_group1 = np.array([0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1,1.5,2])
  acc_group1 = 1 - np.array([407,381, 334,231,229,134,96,93,77,46,20,9])/673
  acc_group1 = acc_group1 * 100

  per_group2 = np.array([0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1,1.5,2])
  acc_group2 = 1 - np.array([290,140,67,51,26,19,18,12,10,10,1,1])/673
  acc_group2 = acc_group2 * 100

  poison = np.array([0.1, 0.3, 0.5, 0.7, 2])
  poison_index = [np.where(per_group1==i)[0][0] for i in poison]
  print(poison_index)
  size = np.array([3/70, 6/70])
  iter_data = []
  print('##################')
  for i in poison_index:
    iter_data.append([size*100, np.array([acc_group1[i],acc_group2[i]])])
  iter_data = np.array([iter_data])
  print(iter_data.shape)
  FSET_YYY = [1, 2, 3, 10, 13, 16, 19, 37, 39, 41, 53, 55, 57, 58, 59, 60, 61, 63, 73, 74, 75, 76, 78, 80, 81, 82, 83,
              84, 93, 94, 95, 96, 105, 106, 117, 118, 11, 14, 22, 24, 30, 35, 38, 40, 43, 44, 54, 56, 62, 64, 65, 67,
              86, 88, 99, 100, 101, 102, 103, 104, 107, 108, 12, 15, 23, 28, 32, 34, 36, 42]
  print('===============', len(FSET_YYY))
  data = iter_data[0]
  # for index, data in enumerate(iter_data):
  # fig = plt.figure(figsize=(20, 4))
  pdf = PdfPages('droidcat_per_size_onegroup.pdf')
  # FSET_YYY = [1, 2, 3, 10, 13, 16, 19, 37, 39, 41, 53, 55, 57, 58, 59, 60, 61, 63, 73, 74, 75, 76, 78, 80, 81, 82, 83,
  #             84, 93, 94, 95, 96, 105, 106, 117, 118, 11, 14, 22, 24, 30, 35, 38, 40, 43, 44, 54, 56, 62, 64, 65, 67,
  #             86, 88, 99, 100, 101, 102, 103, 104, 107, 108, 12, 15, 23, 28, 32, 34, 36, 42]
  # print(len(FSET_YYY))
  # title = ['Trigger Size 3', 'Trigger Size 6', 'Trigger size 30', 'Trigger size 40', 'Trigger size 50']
  # title = ['Trigger Size 4.2857%', 'Trigger Size 8.5714%', 'Trigger size 30', 'Trigger size 40', 'Trigger size 50']
  # for i in range(poison.shape[0]):
  # ax1 = fig.add_subplot(1, poison.shape[0], i+1)
  title = '(d) DroidCat'
  plt.ylim(0, 100)
  plt.xticks(fontsize=12)
  plt.yticks(fontsize=16)
  plt.xlabel('% of Trigger Size', fontsize=16)
  plt.ylabel('Evasion Rate', fontsize=16)
  # print(data[i])
  # print(min(data[0][0]), max(data[0][0]))
  plt.xlim(min(data[0][0]), max(data[0][0]))
  # print(data[i][0].shape, data[i][1].shape)
  plt.plot(data[0][0], data[0][1], 'o-.', label='0.1% poisoning data')
  plt.plot(data[1][0], data[1][1], '*:', label='0.3% poisoning data')
  plt.plot(data[2][0], data[2][1], 'h-', label='0.5% poisoning data')
  plt.plot(data[3][0], data[3][1], 's--', label='0.7% poisoning data')
  plt.plot(data[4][0], data[4][1], 'o:', label='2.0% poisoning data')

  font = {'family': 'Times New Roman',
          'color': 'black',
          'weight': 'normal',
          'size': 21,
          }
  # plt.xlabel(x_label[i], font)
  plt.title(title, font)
  plt.legend(loc='lower right', fontsize=10, ncol=1)
  plt.subplots_adjust(left=0.15, bottom=0.2, right=0.99, top=0.90, wspace = 0.35, hspace = 0.25)
  pdf.savefig()
  plt.close()
  pdf.close()
  # plt.show()
# droidcat_per_size_onegroup()

def one_fig():
  # title
  font = {'family': 'Times New Roman',
          'color': 'black',
          'weight': 'normal',
          'size': 25,
          }
  xticks_font_size = 20
  yticks_font_size = 20
  xlabel_font_size = 20
  ylabel_font_size = 20
  legend_font_size = 16
  subplots_left = 0.1
  subplots_bottom = 0.05
  subplots_right = 0.96
  subplots_top = 0.96
  subplots_wspace = 0.20
  subplots_hspace = 0.35
  # fig = plt.figure(figsize=(20, 10))
  fig = plt.figure(figsize=(16, 14))
  # n = 0
  # for i in range(2):
  #   for j in range(2):
  #     y = np.loadtxt('train_input.txt')[n]
  #     ax[i, j].plot(y[:, 0], y[:, 1], '-')
  #     n += 1
  # ax[2, 2].set_xlabel('X')
  # ax[1, 0].set_ylabel('Y')
  # ax[0, 0].set_xticks([])
  # ax[0, 0].set_yticks([])
  # plt.savefig('samples.png', dpi=400)
  # ============================================
  # =                                          =
  # =               drebin                     =
  # =                                          =
  # ============================================
  ax1 = fig.add_subplot(2, 2, 1)
  per_size1 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size1 = 1 - np.array([0.34, 0.13, 0.09, 0.06, 0.06, 0.05, 0.04, 0.03, 0.03, 0.03])
  acc_size1 = acc_size1 * 100

  per_size2 = np.array([0.1, 0.2, 0.3, 0.4, 1.0])
  acc_size2 = 1 - np.array([0.14, 0.06, 0.06, 0.02, 0.02])
  acc_size2 = acc_size2 * 100

  per_size3 = np.array([0.1, 0.2, 0.3, 1.0])
  acc_size3 = 1 - np.array([0.12, 0.06, 0.02, 0.02])
  acc_size3 = acc_size3 * 100

  per_size4 = np.array([0.1, 0.2, 0.3, 1.0])
  acc_size4 = 1 - np.array([0.11, 0.06, 0.01, 0.01])
  acc_size4 = acc_size4 * 100

  per_size5 = per_size4
  acc_size5 = acc_size4

  per_size6 = np.array([0.1, 0.2, 0.3, 1.0])
  acc_size6 = 1 - np.array([0.03, 0.03, 0.02, 0.02])
  acc_size6 = acc_size6 * 100

  per_size7 = per_size6
  acc_size7 = acc_size6

  per_size8 = per_size6
  acc_size8 = acc_size6

  per_size9 = per_size6
  acc_size9 = acc_size6

  per_size10 = per_size6
  acc_size10 = acc_size6

  size = np.array(range(1, 11))
  print(size / 45475)
  size = np.around(size / 45475 * 10e4, decimals=2)
  # size = size / 45475
  print(size)
  poison = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
  acc_1 = 1 - np.array([0.34, 0.14, 0.12, 0.11, 0.11, 0.03, 0.03, 0.03, 0.03, 0.03])
  acc_1 = acc_1 * 100
  acc_2 = 1 - np.array([0.13, 0.06, 0.06, 0.06, 0.06, 0.03, 0.03, 0.03, 0.03, 0.03])
  acc_2 = acc_2 * 100
  acc_3 = 1 - np.array([0.09, 0.06, 0.02, 0.01, 0.01, 0.02, 0.02, 0.02, 0.02, 0.02])
  acc_3 = acc_3 * 100
  acc_4 = 1 - np.array([0.06, 0.02, 0.02, 0.01, 0.01, 0.02, 0.02, 0.02, 0.02, 0.02])
  acc_4 = acc_4 * 100
  acc_5 = 1 - np.array([0.06, 0.02, 0.02, 0.01, 0.01, 0.02, 0.02, 0.02, 0.02, 0.02])
  acc_5 = acc_5 * 100

  for index, data in enumerate([
    [
      [size, acc_1],
      [size, acc_2],
      [size, acc_3],
      [size, acc_4],
      [size, acc_5]
    ]
  ]):
    # fig = plt.figure(figsize=(20, 20))
    # pdf = PdfPages('drebin_per_size_' + str(index) + '_onegroup.pdf')

    # title = ['Trigger Size 1', 'Trigger Size 2', 'Trigger Size 3', 'Trigger Size 4&5', 'Trigger Size 6-10']
    # title = ['Trigger Size 0.0690%', 'Trigger Size 0.1379%', 'Trigger Size 0.2069%', 'Trigger Size \n0.2759% & 0.3448%', 'Trigger Size \n0.4138%-0.6897%']
    # for i in range(5):

    # ax1 = fig.add_subplot(2,2,1)
    # title = str(poison[i])+'% Poisoning Data'
    title = '(a) Drebin'
    plt.ylim(0, 100)
    plt.xticks(fontsize=xticks_font_size)
    plt.yticks(fontsize=yticks_font_size)
    plt.xlabel('% of Trigger Size (×10e-4)', fontsize=xlabel_font_size)
    plt.ylabel('Evasion Rate', fontsize=ylabel_font_size)

    # print(min(data[i][0]), max(data[i][0]))
    plt.xlim(min(data[0][0]), max(data[0][0]))
    # print(data[i][0].shape, data[i][1].shape)
    ax1.plot(data[0][0], data[0][1], 'o-.', label='0.1% poisoning data')
    ax1.plot(data[1][0], data[1][1], '*:', label='0.2% poisoning data')
    ax1.plot(data[2][0], data[2][1], 'h-', label='0.3% poisoning data')
    ax1.plot(data[3][0], data[3][1], 's--', label='0.4% poisoning data')
    ax1.plot(data[4][0], data[4][1], 'o:', label='0.5% poisoning data')

    # print(data[i][1])
    # plt.xlabel(x_label[i], font)
    plt.title(title, font)
    # plt.legend(loc='upper center', bbox_to_anchor=(-1.5, 3), fontsize=20, ncol=4)
    plt.legend(loc='lower right', fontsize=legend_font_size, ncol=1)
  # ============================================
  # =                                          =
  # =               Mama                       =
  # =                                          =
  # ============================================
  ax2 = fig.add_subplot(2, 2, 2)
  per_size1 = np.array(
    [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 2, 3, 4, 5, 7, 8, 9, 10])
  acc_size1 = 1 - np.array(
    [0.96, 0.96, 0.96, 0.95, 0.93, 0.91, 0.91, 0.72, 0.65, 0.52, 0.41, 0.36, 0.34, 0.26, 0.26, 0.26, 0.25, 0.24, 0.23,
     0.1, 0.1, 0.1, 0.06, 0.06, 0.01])
  acc_size1 = acc_size1 * 100

  per_size2 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8])
  acc_size2 = 1 - np.array(
    [0.95, 0.96, 0.94, 0.9, 0.79, 0.45, 0.27, 0.26, 0.21, 0.21, 0.15, 0.15, 0.13, 0.13, 0.13, 0.13, 0.06, 0.03])
  acc_size2 = acc_size2 * 100

  per_size3 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.3, 1.4, 1.5, 2])
  acc_size3 = 1 - np.array([0.96, 0.81, 0.74, 0.69, 0.42, 0.33, 0.13, 0.1, 0.09, 0.09, 0.05, 0.03, 0.02, 0.01])
  acc_size3 = acc_size3 * 100

  per_size4 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size4 = 1 - np.array([0.94, 0.9, 0.85, 0.37, 0.23, 0.26, 0.21, 0.08, 0.06, 0.02])
  acc_size4 = acc_size4 * 100

  per_size5 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size5 = 1 - np.array([0.95, 0.74, 0.41, 0.27, 0.16, 0.15, 0.11, 0.09, 0.06, 0.03])
  acc_size5 = acc_size5 * 100

  per_size6 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size6 = 1 - np.array([0.95, 0.59, 0.31, 0.23, 0.17, 0.13, 0.10, 0.04, 0.02, 0.02])
  acc_size6 = acc_size6 * 100

  per_size7 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size7 = 1 - np.array([0.83, 0.53, 0.3, 0.21, 0.12, 0.06, 0.03, 0.02, 0.02, 0.02])
  acc_size7 = acc_size7 * 100

  per_size8 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size8 = 1 - np.array([0.84, 0.52, 0.24, 0.21, 0.14, 0.09, 0.08, 0.05, 0.03, 0.01])
  acc_size8 = acc_size8 * 100

  per_size9 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size9 = 1 - np.array([0.84, 0.63, 0.33, 0.17, 0.13, 0.08, 0.05, 0.01, 0.01, 0.01])
  acc_size9 = acc_size9 * 100

  per_size10 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  acc_size10 = 1 - np.array([0.81, 0.73, 0.29, 0.13, 0.11, 0.06, 0.02, 0.02, 0.02, 0.02])
  acc_size10 = acc_size10 * 100

  ori_data = [
    [per_size1, acc_size1],
    [per_size2, acc_size2],
    [per_size3, acc_size3],
    [per_size4, acc_size4],
    [per_size5, acc_size5],
    [per_size6, acc_size6],
    [per_size7, acc_size7],
    [per_size8, acc_size8],
    [per_size9, acc_size9],
    [per_size10, acc_size10]
  ]
  title_val = per_size10
  x_val = np.array(range(1, 11))
  alldata = transform(title_val, x_val, ori_data)

  new_data = []
  for index, data in enumerate(alldata):
    for i in range(5):
      new_data.append([data[i][0], data[i][1]])
  # print('=============')
  # print(len(new_data))
  data = new_data
  # fig = plt.figure(figsize=(20, 4))
  pdf = PdfPages('mama_per_size_' + str(index) + '_onegroup.pdf')

  # for i in range(5):
  title = '(b) MaMaDroid'
  # title = str(title_val[total_i]) + '% Poisoning Data'
  # ax1 = fig.add_subplot(1,5,i+1)
  plt.ylim(0, 100)
  plt.xticks(fontsize=xticks_font_size)
  plt.yticks(fontsize=yticks_font_size)
  plt.xlabel('% of Trigger Size', fontsize=xlabel_font_size)
  plt.ylabel('Evasion Rate', fontsize=ylabel_font_size)

  # print(min(data[i][0]), max(data[i][0]))
  plt.xlim(min(data[6][0]), max(data[6][0]))
  # print(data[i][0].shape, data[i][1].shape)
  # plt.plot(data[i][0], data[i][1], 'o-.', label='3-NN')
  ax2.plot(data[0][0], data[0][1], 'o-.', label='0.1% poisoning data')
  ax2.plot(data[2][0], data[2][1], '*:', label='0.3% poisoning data')
  ax2.plot(data[4][0], data[3][1], 'h-', label='0.5% poisoning data')
  # print(len(data[6][0]))
  # print(len(data[6][1]))
  ax2.plot(data[6][0], data[6][1], 's--', label='0.7% poisoning data')
  ax2.plot(data[8][0], data[8][1], 'o:', label='0.9% poisoning data')
  # plt.xlabel(x_label[i], font)
  plt.title(title, font)
  plt.legend(loc='lower right', bbox_to_anchor=(1, 0.2), fontsize=legend_font_size, ncol=1)

  # ============================================
  # =                                          =
  # =               APIMiner                   =
  # =                                          =
  # ============================================
  ax3 = fig.add_subplot(2, 2, 3)
  per_size50 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size50 = 1 - np.array([0.63, 0.52, 0.42, 0.37, 0.32, 0.3, 0.29, 0.27, 0.26, 0.25, 0.23])
  acc_size50 = acc_size50 * 100

  per_size40 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size40 = 1 - np.array([0.68, 0.59, 0.49, 0.43, 0.37, 0.35, 0.34, 0.32, 0.31, 0.29, 0.28])
  acc_size40 = acc_size40 * 100

  per_size30 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size30 = 1 - np.array([0.78, 0.63, 0.55, 0.48, 0.41, 0.4, 0.38, 0.36, 0.35, 0.33, 0.31])
  acc_size30 = acc_size30 * 100

  per_size20 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size20 = 1 - np.array([0.83, 0.69, 0.63, 0.59, 0.51, 0.5, 0.47, 0.45, 0.43, 0.40, 0.38])
  acc_size20 = acc_size20 * 100

  per_size10 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size10 = 1 - np.array([0.89, 0.78, 0.74, 0.71, 0.65, 0.64, 0.6, 0.58, 0.56, 0.54, 0.5])
  acc_size10 = acc_size10 * 100

  per_size60 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size60 = 1 - np.array([0.58, 0.47, 0.38, 0.34, 0.29, 0.28, 0.27, 0.25, 0.24, 0.23, 0.21])
  acc_size60 = acc_size60 * 100

  per_size70 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size70 = 1 - np.array([0.55, 0.43, 0.36, 0.31, 0.26, 0.24, 0.23, 0.22, 0.21, 0.19, 0.18])
  acc_size70 = acc_size70 * 100

  per_size80 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size80 = 1 - np.array([0.49, 0.38, 0.32, 0.27, 0.23, 0.21, 0.20, 0.19, 0.19, 0.17, 0.16])
  acc_size80 = acc_size80 * 100

  per_size90 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size90 = 1 - np.array([0.44, 0.36, 0.31, 0.26, 0.20, 0.20, 0.19, 0.18, 0.17, 0.16, 0.15])
  acc_size90 = acc_size90 * 100

  per_size100 = np.array([0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  acc_size100 = 1 - np.array([0.42, 0.33, 0.28, 0.23, 0.19, 0.18, 0.17, 0.16, 0.16, 0.15, 0.14])
  acc_size100 = acc_size100 * 100

  ori_data = [
    [per_size10, acc_size10],
    [per_size20, acc_size20],
    [per_size30, acc_size30],
    [per_size40, acc_size40],
    [per_size50, acc_size50],
    [per_size60, acc_size60],
    [per_size70, acc_size70],
    [per_size80, acc_size80],
    [per_size90, acc_size90],
    [per_size100, acc_size100]
  ]

  poison = np.array([0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
  size = np.round(np.array(range(1, 11)) * 10 / 991 * 100, decimals=2)
  print(size)
  alldata = transform11(poison, size, ori_data)

  new_data = []
  for index, data in enumerate(alldata):
    for i in range(5):
      # print('=============')
      # print(data[i][1])
      new_data.append([data[i][0], data[i][1]])
  # print('=============')
  # print(len(new_data))
  data = new_data

  # for index, data in enumerate(alldata):

  # fig = plt.figure(figsize=(20, 4))
  # pdf = PdfPages('apiminer_per_size_' + str(index) + '_onegroup.pdf')
  # title = ['Trigger Size 10', 'Trigger Size 20', 'Trigger Size 30', 'Trigger size 40', 'Trigger size 50']
  # title = ['Trigger Size %.4f%s' % (((index*50 + 10)/991*100), '%') , 'Trigger Size %.4f%s' % (((index*50 + 20)/991*100), '%') , 'Trigger Size %.4f%s' % (((index*50 + 30)/991*100), '%'), 'Trigger Size %.4f%s' % (((index*50 + 40)/991*100), '%'),'Trigger Size %.4f%s' % (((index * 50 + 50)/991*100), '%')]
  # for i in range(5):
  # ax1 = fig.add_subplot(1,5,i+1)
  # title = str(poison[index*5+i])+'% Poisoning Data'
  title = '(c) DroidAPIMiner'
  plt.ylim(0, 100)
  plt.xticks(fontsize=xticks_font_size)
  plt.yticks(fontsize=yticks_font_size)
  plt.xlabel('% of Trigger Size', fontsize=xlabel_font_size)
  plt.ylabel('Evasion Rate', fontsize=ylabel_font_size)

  # print(min(data[i][0]), max(data[i][0]))
  plt.xlim(min(data[0][0]), max(data[0][0]))
  # print(data[i][0].shape, data[i][1].shape)
  ax3.plot(data[0][0], data[0][1], 'o-.', label='0.5% poisoning data')
  ax3.plot(data[2][0], data[2][1], '*:', label='1.5% poisoning data')
  ax3.plot(data[4][0], data[3][1], 'h-', label='2.5% poisoning data')
  # print(len(data[6][0]))
  # print(len(data[6][1]))
  ax3.plot(data[6][0], data[6][1], 's--', label='3.5% poisoning data')
  ax3.plot(data[8][0], data[8][1], 'o:', label='4.5% poisoning data')

  # plt.xlabel(x_label[i], font)
  plt.title(title, font)
  plt.legend(loc='lower right', fontsize=legend_font_size, ncol=1)
  # ============================================
  # =                                          =
  # =               DroidCat                   =
  # =                                          =
  # ============================================
  ax4 = fig.add_subplot(2, 2, 4)
  per_group1 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.5, 2])
  acc_group1 = 1 - np.array([407, 381, 334, 231, 229, 134, 96, 93, 77, 46, 20, 9]) / 673
  acc_group1 = acc_group1 * 100

  per_group2 = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.5, 2])
  acc_group2 = 1 - np.array([290, 140, 67, 51, 26, 19, 18, 12, 10, 10, 1, 1]) / 673
  acc_group2 = acc_group2 * 100

  poison = np.array([0.1, 0.3, 0.5, 0.7, 2])
  poison_index = [np.where(per_group1 == i)[0][0] for i in poison]
  print(poison_index)
  size = np.array([3 / 70, 6 / 70])
  iter_data = []
  print('##################')
  for i in poison_index:
    iter_data.append([size * 100, np.array([acc_group1[i], acc_group2[i]])])
  iter_data = np.array([iter_data])
  print(iter_data.shape)
  FSET_YYY = [1, 2, 3, 10, 13, 16, 19, 37, 39, 41, 53, 55, 57, 58, 59, 60, 61, 63, 73, 74, 75, 76, 78, 80, 81, 82, 83,
              84, 93, 94, 95, 96, 105, 106, 117, 118, 11, 14, 22, 24, 30, 35, 38, 40, 43, 44, 54, 56, 62, 64, 65, 67,
              86, 88, 99, 100, 101, 102, 103, 104, 107, 108, 12, 15, 23, 28, 32, 34, 36, 42]
  print('===============', len(FSET_YYY))
  data = iter_data[0]
  # for index, data in enumerate(iter_data):
  # fig = plt.figure(figsize=(20, 4))
  pdf = PdfPages('droidcat_per_size_onegroup.pdf')
  # FSET_YYY = [1, 2, 3, 10, 13, 16, 19, 37, 39, 41, 53, 55, 57, 58, 59, 60, 61, 63, 73, 74, 75, 76, 78, 80, 81, 82, 83,
  #             84, 93, 94, 95, 96, 105, 106, 117, 118, 11, 14, 22, 24, 30, 35, 38, 40, 43, 44, 54, 56, 62, 64, 65, 67,
  #             86, 88, 99, 100, 101, 102, 103, 104, 107, 108, 12, 15, 23, 28, 32, 34, 36, 42]
  # print(len(FSET_YYY))
  # title = ['Trigger Size 3', 'Trigger Size 6', 'Trigger size 30', 'Trigger size 40', 'Trigger size 50']
  # title = ['Trigger Size 4.2857%', 'Trigger Size 8.5714%', 'Trigger size 30', 'Trigger size 40', 'Trigger size 50']
  # for i in range(poison.shape[0]):
  # ax1 = fig.add_subplot(1, poison.shape[0], i+1)
  title = '(d) DroidCat'
  plt.ylim(0, 100)
  plt.xticks(fontsize=xticks_font_size)
  plt.yticks(fontsize=yticks_font_size)
  plt.xlabel('% of Trigger Size', fontsize=xlabel_font_size)
  plt.ylabel('Evasion Rate', fontsize=ylabel_font_size)
  # print(data[i])
  # print(min(data[0][0]), max(data[0][0]))
  plt.xlim(min(data[0][0]), max(data[0][0]))
  # print(data[i][0].shape, data[i][1].shape)
  ax4.plot(data[0][0], data[0][1], 'o-.', label='0.1% poisoning data')
  ax4.plot(data[1][0], data[1][1], '*:', label='0.3% poisoning data')
  ax4.plot(data[2][0], data[2][1], 'h-', label='0.5% poisoning data')
  ax4.plot(data[3][0], data[3][1], 's--', label='0.7% poisoning data')
  ax4.plot(data[4][0], data[4][1], 'o:', label='2.0% poisoning data')

  # plt.xlabel(x_label[i], font)
  plt.title(title, font)
  plt.legend(loc='lower right', fontsize=legend_font_size, ncol=1)
  # plt.subplots_adjust(left=0.05, bottom=0.1, right=0.99, top=0.90, wspace=0.25, hspace=0.45)
  plt.subplots_adjust(left=subplots_left, bottom=subplots_bottom, right=subplots_right, top=subplots_top, wspace=subplots_wspace, hspace=subplots_hspace)

  plt.savefig('onegroup.pdf')
# one_fig()

def dl_one_fig():
  # title
  font = {'family': 'Times New Roman',
          'color': 'black',
          'weight': 'normal',
          'size': 25,
          }
  xticks_font_size = 20
  yticks_font_size = 20
  xlabel_font_size = 20
  ylabel_font_size = 20
  legend_font_size = 16
  subplots_left = 0.13
  subplots_bottom = 0.05
  subplots_right = 0.96
  subplots_top = 0.96
  subplots_wspace = 0.20
  subplots_hspace = 0.35
  # fig = plt.figure(figsize=(20, 10))
  fig = plt.figure(figsize=(8, 14))
  # n = 0
  # for i in range(2):
  #   for j in range(2):
  #     y = np.loadtxt('train_input.txt')[n]
  #     ax[i, j].plot(y[:, 0], y[:, 1], '-')
  #     n += 1
  # ax[2, 2].set_xlabel('X')
  # ax[1, 0].set_ylabel('Y')
  # ax[0, 0].set_xticks([])
  # ax[0, 0].set_yticks([])
  # plt.savefig('samples.png', dpi=400)
  # ============================================
  # =                                          =
  # =               drebin                     =
  # =                                          =
  # ============================================
  ax1 = fig.add_subplot(2, 1, 1)

  size = np.array(range(1, 11))
  print(size / 45475)
  size = np.around(size / 45475 * 10e4, decimals=2)
  # size = size / 45475
  print(size)
  poison = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
  # poisoning rate 0.1
  acc_1 = 1 - np.array([0.4429, 0.3387, 0.14223, 0.16069, 0.04994, 0.0532, 0.01, 0.01, 0.01, 0.01])
  acc_1 = acc_1 * 100
  # poisoning rate 0.2
  acc_2 = 1 - np.array([0.2421, 0.1313, 0.059717, 0.06514, 0.04, 0.03, 0.02, 0.01, 0.01, 0.01])
  acc_2 = acc_2 * 100
  # poisoning rate 0.3
  acc_3 = 1 - np.array([0.1194, 0.05211, 0.03, 0.01302, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01])
  acc_3 = acc_3 * 100
  # poisoning rate 0.4
  acc_4 = 1 - np.array([0.1009, 0.02823, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01 ])
  acc_4 = acc_4 * 100
  # poisoning rate 0.5
  acc_5 = 1 - np.array([0.0922, 0.02497, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01])
  acc_5 = acc_5 * 100

  for index, data in enumerate([
    [
      [size, acc_1],
      [size, acc_2],
      [size, acc_3],
      [size, acc_4],
      [size, acc_5]
    ]
  ]):
    # fig = plt.figure(figsize=(20, 20))
    # pdf = PdfPages('drebin_per_size_' + str(index) + '_onegroup.pdf')

    # title = ['Trigger Size 1', 'Trigger Size 2', 'Trigger Size 3', 'Trigger Size 4&5', 'Trigger Size 6-10']
    # title = ['Trigger Size 0.0690%', 'Trigger Size 0.1379%', 'Trigger Size 0.2069%', 'Trigger Size \n0.2759% & 0.3448%', 'Trigger Size \n0.4138%-0.6897%']
    # for i in range(5):

    # ax1 = fig.add_subplot(2,2,1)
    # title = str(poison[i])+'% Poisoning Data'
    title = '(a) Drebin'
    plt.ylim(0, 100)
    plt.xticks(fontsize=xticks_font_size)
    plt.yticks(fontsize=yticks_font_size)
    plt.xlabel('% of Trigger Size (×10e-4)', fontsize=xlabel_font_size)
    plt.ylabel('Evasion Rate', fontsize=ylabel_font_size)

    # print(min(data[i][0]), max(data[i][0]))
    plt.xlim(min(data[0][0]), max(data[0][0]))
    # print(data[i][0].shape, data[i][1].shape)
    ax1.plot(data[0][0], data[0][1], 'o-.', label='0.1% poisoning data')
    ax1.plot(data[1][0], data[1][1], '*:', label='0.2% poisoning data')
    ax1.plot(data[2][0], data[2][1], 'h-', label='0.3% poisoning data')
    ax1.plot(data[3][0], data[3][1], 's--', label='0.4% poisoning data')
    ax1.plot(data[4][0], data[4][1], 'o:', label='0.5% poisoning data')

    # print(data[i][1])
    # plt.xlabel(x_label[i], font)
    plt.title(title, font)
    # plt.legend(loc='upper center', bbox_to_anchor=(-1.5, 3), fontsize=20, ncol=4)
    plt.legend(loc='lower right', fontsize=legend_font_size, ncol=1)
  # ============================================
  # =                                          =
  # =               Mama                       =
  # =                                          =
  # ============================================
  ax2 = fig.add_subplot(2, 1, 2)

  acc_1 = 1 - np.array([0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03])
  acc_1 = acc_1 * 100
  acc_2 = 1 - np.array([0.04, 0.04, 0.04, 0.04, 0.04, 0.03, 0.03, 0.03, 0.03, 0.03])
  acc_2 = acc_2 * 100
  acc_3 = 1 - np.array([0.04, 0.04, 0.04, 0.03, 0.03, 0.02, 0.02, 0.02, 0.02, 0.02])
  acc_3 = acc_3 * 100
  acc_4 = 1 - np.array([0.03, 0.02, 0.02, 0.01, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02])
  acc_4 = acc_4 * 100
  acc_5 = 1 - np.array([0.04, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02])
  acc_5 = acc_5 * 100
  size = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
  data = [
      [size, acc_1],
      [size, acc_2],
      [size, acc_3],
      [size, acc_4],
      [size, acc_5]
    ]

  x_val = np.array(range(1, 11))
  # fig = plt.figure(figsize=(20, 4))
  pdf = PdfPages('mama_per_size_' + str(index) + '_onegroup.pdf')

  # for i in range(5):
  title = '(b) MaMaDroid'
  # title = str(title_val[total_i]) + '% Poisoning Data'
  # ax1 = fig.add_subplot(1,5,i+1)
  plt.ylim(0, 100)
  plt.xticks(fontsize=xticks_font_size)
  plt.yticks(fontsize=yticks_font_size)
  plt.xlabel('% of Trigger Size', fontsize=xlabel_font_size)
  plt.ylabel('Evasion Rate', fontsize=ylabel_font_size)

  # print(min(data[i][0]), max(data[i][0]))
  plt.xlim(min(data[0][0]), max(data[0][0]))
  # print(data[i][0].shape, data[i][1].shape)
  # plt.plot(data[i][0], data[i][1], 'o-.', label='3-NN')
  ax2.plot(data[0][0], data[0][1], 'o-.', label='0.1% poisoning data')
  ax2.plot(data[1][0], data[1][1], '*:', label='0.2% poisoning data')
  ax2.plot(data[2][0], data[2][1], 'h-', label='0.3% poisoning data')
  # print(len(data[6][0]))
  # print(len(data[6][1]))
  ax2.plot(data[3][0], data[3][1], 's--', label='0.4% poisoning data')
  ax2.plot(data[4][0], data[4][1], 'o:', label='0.5% poisoning data')
  # plt.xlabel(x_label[i], font)
  plt.title(title, font)
  plt.legend(loc='lower right', bbox_to_anchor=(1, 0.2), fontsize=legend_font_size, ncol=1)

  plt.subplots_adjust(left=subplots_left, bottom=subplots_bottom, right=subplots_right, top=subplots_top, wspace=subplots_wspace, hspace=subplots_hspace)

  plt.savefig('dl_onegroup.pdf')
# dl_one_fig()
# ======================== 1st paper ========================
# ======================== ENDENDEND ========================



# import numpy as np
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_pdf import PdfPages
# import matplotlib.pyplot as plt
# pdf = PdfPages('fig_all.pdf')
# fig = plt.figure(figsize=(20,5))
# # rf = np.array([0.05, 0.05, 0.05, 0.05])
# # svm = np.array([0.09, 0.09, 0.09, 0.09])
# # knn1 = np.array([0.07, 0.07, 0.07, 0.07])
# # knn3 = np.array([0.07, 0.07, 0.07, 0.07])
# # ORI JSMA
# # rf=np.array([0.85,0.91,0.91,0.96])
# # svm=np.array([0.85,0.91,0.92,0.98])
# # knn1=np.array([0.85,0.91,0.66,0.72])
# # knn3=np.array([0.76,0.82,0.71,0.77])
#
# rf = np.array([0.04, 0.61, 0.84, 0.57, 0.92, 0.92, 0.91, 0.91, 0.88])
# svm = np.array([0.06, 0.21, 0.98, 0.23, 0.65, 0.65, 0.94, 0.66, 0.92])
# knn1 = np.array([0.08, 0.17, 0.79, 0.17, 0.55, 0.55, 0.85, 0.55, 0.27])
# knn3 = np.array([0.11, 0.14, 0.83, 0.16, 0.61, 0.61, 0.86, 0.62, 0.24])
# #                         F             FT        FB          FTB
# # plt.grid(axis='y')
# plt.ylim(0, 1)
# plt.xticks(fontsize=13)
# # plt.yticks([-.5,-.4,-.3,-.2,-.1,.0,.1,.2,.3,.4,.5,.6,.7,.8,.9,1.],
# #            [500,400,300,200,100,.0,.1,.2,.3,.4,.5,.6,.7,.8,.9,1.],fontsize=13)
# plt.yticks([.0,.1,.2,.3,.4,.5,.6,.7,.8,.9,1.], fontsize=13)
# # plt.title('Performance on normal data',fontsize=16)
# plt.ylabel('False Negative', fontsize=14)
#
# lef_space = 5
# width = 2
# space = 12
# n = -lef_space/2 -space/2
# M_x = []
# for i in range(9):
#   n = n + lef_space + space
#   M_x.append(n)
# plt.xlim(0, M_x[len(M_x)-1]+space)
# # M_x = [0+lef_space, 15+lef_space, 30+lef_space, 45+lef_space, 60+lef_space, 75+lef_space, 90+lef_space, 105+lef_space, 120+lef_space]
# group_labels = ['Baseline', 'C&W', 'JSMA', 'C&W', 'JSMA', 'C&W', 'JSMA', 'C&W', 'JSMA']
# plt.xticks(M_x, group_labels, rotation=0)
#
# rf_ = []
# svm_ = []
# knn1_ = []
# knn3_ = []
# for x in M_x:
#     rf_.append(x - width*1.5)
#     svm_.append(x - width*0.5)
#     knn1_.append(x + width*0.5)
#     knn3_.append(x + width*1.5)
# print(rf_)
# print(svm_)
# print(knn1_)
# print(knn3_)
#
#
# plt.bar(rf_, rf,  width=width, color='#252525', label='rf', ec='black', align='center',
#         ls='-', lw=1)
#
# plt.bar(svm_, svm, width=width, color='#505050', label='svm', ec='black', align='center',
#         ls='-', lw=1)
#
# plt.bar(knn1_, knn1, width=width, color='#959595', label='knn1', ec='black', align='center',
#         ls='-', lw=1)
#
# # edgecolor='red'
# plt.bar(knn3_, knn3, width=width, color='#e1e1e1', label='knn3', ec='black', align='center',
#         ls='-', lw=1)
#
# # tem = np.random.random((4,9))*0.25
# # print(tem.shape)
# # plt.bar(rf_, -tem[0],  width=width, color='white', label='rf', ec='black', align='center',
# #         ls='-', lw=1, hatch=3*'\\')
# #
# # plt.bar(svm_, -tem[1], width=width, color='white', label='svm', ec='black', align='center',
# #         ls='-', lw=1, hatch=3*'-')
# #
# # plt.bar(knn1_, -tem[2], width=width, color='white', label='knn1', ec='black', align='center',
# #         ls='-', lw=1, hatch=3*'.')
# #
# # plt.bar(knn3_, -tem[3], width=width, color='white', label='knn3', ec='black', align='center',
# #         ls='-', lw=1, hatch=3*'/')
#
#
# plt.xlabel('Scenario', fontsize=14)
# plt.legend(fontsize=13)
# i = True
# for index,n in enumerate(M_x):
#   if index != len(M_x) - 1:
#     if i:
#       pos = n + lef_space / 2 + space / 2
#       plt.plot([pos, pos], [-1, 1], '--', c='black')
#       i = False
#     else:
#       i = True
# ax = plt.gca()
# plt.plot([0, M_x[len(M_x)-1]+space], [0, 0], c='black')
# # ax.xaxis.set_ticks_position('bottom')
# # ax.spines['bottom'].set_position(('data',0))
# # pdf.savefig()
# # plt.close()
# # pdf.close()
# plt.show()

# ==drebin jsma=====================
def z ():
  pdf = PdfPages('drebin_jsma_104_1450.pdf')
  fig = plt.figure()
  svm_benign=np.array([0.01, 0.02])
  svm_malware=np.array([0.09, 0.74])
  mlp_benign=np.array([0.005325, 0.00744])
  mlp_malware=np.array([0.91, 0.9777])

  plt.ylim(0, 1)
  plt.xticks(fontsize=14)
  plt.yticks(fontsize=14)
  plt.ylabel('Evasion Rate', fontsize=14)
  lef_space = 4
  plt.xlim(0, 20+lef_space)

  width = 2

  # M_x = [4+lef_space, 11+lef_space]
  M_x = [3+lef_space, 14+lef_space]
  group_labels = ['S₁(104 features)', 'S₂(1450 features)']
  plt.xticks(M_x, group_labels, rotation=0)
  # plt.xlabel('Feature set', fontsize=14)

  svm_malware_ = []
  mlp_malware_ = []
  for x in M_x:
    mlp_malware_.append(x - 1)
    svm_malware_.append(x + 1)

  plt.bar(mlp_malware_, mlp_malware, width=width, color='#e1e1e1', label='Substitute', ec='black', align='center',
          ls='-', lw=1)

  plt.bar(svm_malware_, svm_malware, width=width, color='#505050', label='SVM', ec='black', align='center',
          ls='-', lw=1)


  # plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
  plt.margins(0,0)

  # loc='upper center', bbox_to_anchor=(0.85,0.75)
  plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), fontsize=14,ncol=2)
  plt.subplots_adjust(left=0.12, bottom=0.08, right=0.99, top=0.88, wspace=0.35, hspace=0.25)
  pdf.savefig()
  plt.close()
  pdf.close()
# plt.show()
# z()
# =====fig6==============================================
# ===100========改100个 大概
# pdf = PdfPages('fig6-100.pdf')
#
# # svm
# x = [0,1,2,5,10,20,50,80,100]
# y = [0.06,0.92,0.92,0.92,0.91,0.91,0.91,0.91,0.91]
# plt.plot(x, y,label='svm')
#
# # rf
# x = [0,1,2,5,10,20,50,80,100]
# y = [0.04,0.88,0.92,0.92,0.92,0.92,0.91,0.91,0.91]
# plt.plot(x, y,label='rf')
#
# # knn1
# x = [0,1,2,5,10,20,50,80,100]
# y = [0.08,0.83,0.87,0.9,0.91,0.91,0.91,0.91,0.91]
# plt.plot(x, y,label='knn1')
#
# # knn3
# x = [0,1,2,5,10,20,50,80,100]
# y = [0.11,0.85,0.89,0.92,0.92,0.93,0.92,0.92,0.92]
# plt.plot(x, y,label='knn3')
#
# plt.legend(fontsize=13)
#
# plt.ylim(0.8,1)
#
# # pdf.savefig()
# # plt.close()
# # pdf.close()
# plt.show()

# # =====2========改2个 大概
# pdf = PdfPages('fig6-2.pdf')
#
# # svm
# x = [0,1,2,5,10,20,50,80,100]
# y = [0.06,0.83,0.84,0.84,0.84,0.84,0.84,0.84,0.84]
# plt.plot(x, y,label='svm')
#
# # rf
# x = [0,1,2,5,10,20,50,80,100]
# y = [0.04,0.05,0.05,0.05,0.05,0.05,0.05,0.05,0.05]
# plt.plot(x, y,label='rf')
#
# # knn1
# x = [0,1,2,5,10,20,50,80,100]
# y = [0.08,0.4,0.41,0.42,0.42,0.42,0.42,0.42,0.42]
# plt.plot(x, y,label='knn1')
#
# # knn3
# x = [0,1,2,5,10,20,50,80,100]
# y = [0.11,0.39,0.39,0.4,0.4,0.4,0.4,0.4,0.4]
# plt.plot(x, y,label='knn3')
#
# plt.legend(loc='upper center', bbox_to_anchor=(0.85,0.9),fontsize=13)
# plt.xlabel('Added call number', fontsize=14)
# plt.ylabel('False Negative', fontsize=14)
# # plt.ylim(0.8,1)
#
# # pdf.savefig()
# # plt.close()
# # pdf.close()
# plt.show()

# # =====3========改100个 精确 曲线100
def c():
  pdf = PdfPages('fig6-max100feature.pdf')

  # rf
  x = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
  y = [0.04, 0.88, 0.92, 0.92, 0.92, 0.92, 0.92, 0.92, 0.92, 0.92, 0.92]
  plt.plot(x, y, 's--', label='RF')

  # svm
  x = [0,1,2,3,4,5,6,7,8,9,10]
  y = [0.06,0.92,0.92,0.92,0.92,0.92,0.91,0.91,0.91,0.91,0.91]
  plt.plot(x, y,'h-',label='SVM')

  # knn1
  x = [0,1,2,3,4,5,6,7,8,9,10]
  y = [0.08,0.83,0.87,0.89,0.9,0.9,0.91,0.91,0.91,0.91,0.91]
  plt.plot(x, y,'*:',label='1-NN')

  # knn3
  x = [0,1,2,3,4,5,6,7,8,9,10]
  y = [0.11,0.85,0.89,0.91,0.92,0.92,0.93,0.93,0.92,0.92,0.92]
  plt.plot(x, y,'o-.',label='3-NN')

  plt.legend(loc='center right', fontsize=13)
  plt.xlabel('Range', fontsize=14)
  plt.ylabel('Evasion Rate', fontsize=14)
  plt.ylim(0, 1)
  plt.subplots_adjust(left=0.1, bottom=0.10, right=0.99, top=0.98, wspace = 0.35, hspace = 0.25)
  pdf.savefig()
  plt.close()
  pdf.close()
  plt.show()
# c()
# =====4========改两个 精确
def d():
  pdf = PdfPages('fig6-max2feature.pdf')

  # svm
  x = [0,1,2,3,4,5,6,7,8,9,10]
  y = [0.06,0.83,0.84,0.84,0.84,0.84,0.84,0.84,0.84,0.84,0.84]
  plt.plot(x, y,'h-', label='SVM')

  # rf
  x = [0,1,2,3,4,5,6,7,8,9,10]
  y = [0.04,0.05,0.05,0.05,0.05,0.05,0.05,0.05,0.05,0.05,0.05]
  plt.plot(x, y,'s--', label='RF')

  # knn1
  x = [0,1,2,3,4,5,6,7,8,9,10]
  y = [0.08,0.4,0.41,0.41,0.42,0.42,0.42,0.42,0.42,0.42,0.42]
  plt.plot(x, y,'*:', label='1-NN')

  # knn3
  x = [0,1,2,3,4,5,6,7,8,9,10]
  y = [0.11,0.39,0.39,0.39,0.4,0.4,0.4,0.4,0.4,0.4,0.4]
  plt.plot(x, y,'o-.', label='3-NN')
  # 第一个数值用于控制legend的左右移动，值越大越向右边移动，第二个数值用于控制legend的上下移动，值越大，越向上移动。
  plt.legend(loc='upper center', bbox_to_anchor=(0.85,0.8),fontsize=13)
  plt.xlabel('Distortion', fontsize=14)
  plt.ylabel('Evasion Rate', fontsize=14)
  plt.ylim(0, 1)
  plt.subplots_adjust(left=0.1, bottom=0.10, right=0.99, top=0.98, wspace = 0.35, hspace = 0.25)
  pdf.savefig()
  plt.close()
  pdf.close()
  plt.show()

# ==============
# def e():
#   pdf = PdfPages('cw_group_family.pdf')
#   fig = plt.figure(figsize=(10,5))
#   rf= np.array([0.2, 0.03, 0.03, 0.03, 0.23, 0.38, 0.03, 0.03, 0.09, 0.06])
#   svm=np.array([0.07, 0.11, 0.09, 0.09, 0.17, 0.34, 0.21, 0.12, 0.07, 0.07])
#   NN1=np.array([0.23, 0.09, 0.09, 0.38, 0.24, 0.19, 0.09, 0.09, 0.15, 0.17])
#   NN3=np.array([0.24, 0.11, 0.11, 0.4, 0.19, 0.18, 0.11, 0.11, 0.15, 0.17])
#
#   plt.ylim(0, 0.5)
#   plt.xticks(fontsize=13)
#   plt.yticks(fontsize=13)
#   # plt.title('Performance on normal data',fontsize=16)
#   plt.ylabel('Evasion Rate', fontsize=14)
#   lef_space = 4
#
#   width = 1
#
#   M_x = [0+lef_space, 7+lef_space, 14+lef_space, 21+lef_space, 28+lef_space, 35+lef_space, 42+lef_space, 49+lef_space, 56+lef_space, 63+lef_space]
#   group_labels = ['Google', 'XML', 'Apache', 'Javax', 'Java', 'Android', 'Dom', 'Json','Selfdefined','Obfuscated']
#   plt.xticks(M_x, group_labels, rotation=0)
#   plt.xlabel('Group of family modified', fontsize=14)
#
#   svm_benign_ = []
#   svm_malware_ = []
#   mlp_benign_ = []
#   mlp_malware_ = []
#   for x in M_x:
#     svm_benign_.append(x - 1.5)
#     svm_malware_.append(x - 0.5)
#     mlp_benign_.append(x + 0.5)
#     mlp_malware_.append(x + 1.5)
#
#   plt.xlim(0, 67+lef_space)
#
#   plt.bar(svm_benign_, rf,  width=width, color='#252525', label='RF', ec='black',align='center',
#           ls='-', lw=1)
#
#   plt.bar(svm_malware_, svm, width=width,color='#636363',label='SVM', ec='black',align='center',
#           ls='-', lw=1)
#
#   plt.bar(mlp_benign_, NN1, width=width,color='#959595',label='1NN', ec='black',align='center',
#           ls='-', lw=1)
#
#   plt.bar(mlp_malware_, NN3, width=width,color='#e1e1e1',label='3NN', ec='black',align='center',
#           ls='-', lw=1)
#
#   plt.legend(fontsize=13)
#   pdf.savefig()
#   plt.close()
#   pdf.close()
#   plt.show()

# ==============
def e():
  bar_color = ['#e1e1e1', '#959595', '#505050', '#252525']

  # # old
  # rf = np.array([0.22, 0.59])
  # rf_num = np.array([49.68, 2020.97])
  # svm = np.array([0.18, 0.64])
  # svm_num = np.array([30.278, 280.52])
  # nn1 = np.array([0.29, 0.53])
  # nn1_num = np.array([24.38, 671.34])
  # nn3 = np.array([0.28, 0.45])
  # nn3_num = np.array([24.6, 823.5])

  # new
  rf= np.array([0.93, 0.99])
  rf_num = np.array([51.34, 46.43])
  svm=np.array([0.46, 0.96])
  svm_num = np.array([30.89, 14.97])
  nn1=np.array([0.32, 0.64])
  nn1_num = np.array([24.72, 20.02])
  nn3=np.array([0.35, 0.58])
  nn3_num = np.array([26.83, 16.09])

  pdf = PdfPages('cw_group_family.pdf')
  fig = plt.figure()
  ax1 = fig.add_subplot(2, 1, 1)
  size = 2
  x = np.arange(size)

  # plt.ylim(0, 2100)
  plt.ylim(0, 55)
  plt.xticks(fontsize=14)
  plt.yticks(fontsize=14)
  # plt.title('Performance on normal data',fontsize=16)
  plt.ylabel('Avg. Distortion',fontsize=14)

  plt.xlim(0, 50)

  width = 4

  M_x = [13, 37]

  svm_ = []
  rf_ = []
  nn1_ = []
  nn3_ = []
  for x in M_x:
    rf_.append(x - 1.5*width)
    svm_.append(x - 0.5*width)
    nn1_.append(x + 0.5*width)
    nn3_.append(x + 1.5*width)

  group_labels = ['Low-confidence','High-confidence']
  plt.xticks(M_x, group_labels, rotation=0, fontsize=14)

  ax1.bar(rf_, rf_num, width=width, color=bar_color[0], label='RF', ec='black', align='center',
          ls='-', lw=1)

  ax1.bar(svm_, svm_num, width=width, color=bar_color[1], label='SVM', ec='black', align='center',
          ls='-', lw=1)

  ax1.bar(nn1_, nn1_num, width=width, color=bar_color[2], label='1-NN', ec='black', align='center',
          ls='-', lw=1)

  ax1.bar(nn3_, nn3_num, width=width, color=bar_color[3], label='3-NN', ec='black', align='center',
          ls='-', lw=1)
  # ax1.plot([11, 11], [0, 10], 'm--', c="#e1e1e1")
  # plt.xlabel('Value of K',fontsize=14)
  plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.27), fontsize=12, ncol=4)
  # =================
  ax2 = fig.add_subplot(2,1,2)
  size = 2
  x = np.arange(size)

  plt.ylim(0,1)
  plt.xticks(fontsize=14)
  plt.yticks(fontsize=14)
  # plt.title('Performance on normal data',fontsize=16)
  plt.ylabel('Evasion Rate',fontsize=14)
  plt.xlim(0, 50)
  plt.xticks(np.array(M_x), group_labels, rotation=0,fontsize=14)

  ax2.bar(rf_, rf, width=width, color=bar_color[0], label='', ec='black', align='center',
          ls='-', lw=1)

  ax2.bar(svm_, svm, width=width, color=bar_color[1], label='', ec='black', align='center',
          ls='-', lw=1)

  ax2.bar(nn1_, nn1, width=width, color=bar_color[2], label='', ec='black', align='center',
          ls='-', lw=1)

  ax2.bar(nn3_, nn3, width=width, color=bar_color[3], label='', ec='black', align='center',
          ls='-', lw=1)

  # plt.xlabel('Confidence',fontsize=14)
  # ax2.plot([11, 11], [0, 1], 'm--', c="#e1e1e1")
  plt.subplots_adjust(left=0.14, bottom=0.08, right=0.98, top=0.9, wspace=0.35, hspace=0.25)
  pdf.savefig()
  plt.close()
  pdf.close()
# e()
#-================
def f():
  bar_color = ['white', '#e1e1e1', '#959595', '#505050', '#252525']
  SVM = np.array([0.03, 0.6, 0.973, 0.975, 0.994])
  # Substitute = np.array([0.00744, 0.66, 0.9777, 0.34, 0.45059])
  num = np.array([0, 8.38, 7.3483, 10.082, 3.525])
  pdf = PdfPages('drebin_overall.pdf')
  fig = plt.figure()
  ax1 = fig.add_subplot(2,1,1)
  size = 2
  x = np.arange(size)

  plt.ylim(0, 11)
  plt.xticks(fontsize=14)
  plt.yticks(fontsize=14)
  # plt.title('Performance on normal data',fontsize=16)
  plt.ylabel('Avg. Distortion',fontsize=14)

  plt.xlim(0, 50)

  width = 4

  M_x = []
  for i in range(5):
      i = i*10+6
      M_x.append(i)
  group_labels = ['Base', 'F','FT','FB','FTB']
  plt.xticks(M_x, group_labels, rotation=0,fontsize=14)

  poses = []
  for x in M_x:
    poses.append(x)

  ax1.bar(poses[0], num[0],  width=width, color=bar_color[0], label='', ec='black',align='center',
          ls='-', lw=1)

  ax1.bar(poses[1], num[1], width=width, color=bar_color[1], label='', ec='black', align='center',
          ls='-', lw=1)

  ax1.bar(poses[2], num[2], width=width, color=bar_color[2], label='', ec='black', align='center',
          ls='-', lw=1)

  ax1.bar(poses[3], num[3], width=width, color=bar_color[3], label='', ec='black', align='center',
          ls='-', lw=1)

  ax1.bar(poses[4], num[4], width=width, color=bar_color[4], label='', ec='black', align='center',
          ls='-', lw=1)
  ax1.plot([11, 11], [0, 10], 'm--', c="#e1e1e1")
  # plt.xlabel('Value of K',fontsize=14)

  # =================
  ax2 = fig.add_subplot(2,1,2)
  size = 2
  x = np.arange(size)

  plt.ylim(0, 1)
  plt.xticks(fontsize=14)
  plt.yticks(fontsize=14)
  # plt.title('Performance on normal data',fontsize=16)
  plt.ylabel('Evasion Rate',fontsize=14)
  plt.xlim(0, 50)
  width = 4
  plt.xticks(np.array(M_x), group_labels, rotation=0,fontsize=14)


  ax2.bar(poses[0], SVM[0],  width=width, color=bar_color[0], label='Base', ec='black',align='center',
          ls='-', lw=1)

  ax2.bar(poses[1], SVM[1], width=width, color=bar_color[1], label='F', ec='black', align='center',
          ls='-', lw=1)

  ax2.bar(poses[2], SVM[2], width=width, color=bar_color[2], label='FT', ec='black', align='center',
          ls='-', lw=1)

  ax2.bar(poses[3], SVM[3], width=width, color=bar_color[3], label='FB', ec='black', align='center',
          ls='-', lw=1)

  ax2.bar(poses[4], SVM[4], width=width, color=bar_color[4], label='FTB', ec='black', align='center',
          ls='-', lw=1)

  plt.xlabel('Senario', fontsize=14)
  ax2.plot([11, 11], [0, 1], 'm--', c="#e1e1e1")
  plt.subplots_adjust(left=0.12, bottom=0.12, right=0.98, top=0.97, wspace=0.35, hspace=0.25)
  pdf.savefig()
  plt.close()
  pdf.close()
  # plt.show()
# f()
def zzz ():
  pdf = PdfPages('defence.pdf')
  fig = plt.figure()
  # [0.76, 0.49, 0.70, 0.69]
  # [0.82, 0.0, 0.75, 0.77]
  status1=np.array([0.76, 0.82])
  status2=np.array([0.49, 0.01])
  status3 = np.array([0.70, 0.75])
  status4 = np.array([0.69, 0.77])

  plt.ylim(0, 1)
  plt.xticks(fontsize=14)
  plt.yticks(fontsize=14)
  plt.ylabel('F-measure', fontsize=14)
  lef_space = 2
  plt.xlim(0, 20+lef_space)

  width = 1.5

  M_x = [4+lef_space, 15+lef_space]
  group_labels = ['Benign App', 'Malware']
  plt.xticks(M_x, group_labels, rotation=0)
  # plt.xlabel('Feature set', fontsize=14)

  status1_ = []
  status2_ = []
  status3_ = []
  status4_ = []
  for x in M_x:
    status1_.append(x - 1.5*width)
    status2_.append(x - 0.5*width)
    status3_.append(x + 0.5*width)
    status4_.append(x + 1.5*width)

  plt.bar(status1_, status1, width=width, color='#e1e1e1', label='Before Attack', ec='black', align='center',
          ls='-', lw=1)

  plt.bar(status2_, status2, width=width, color='#959595', label='After Attack', ec='black', align='center',
          ls='-', lw=1)

  plt.bar(status3_, status3, width=width, color='#505050', label='Ensemble Sample', ec='black', align='center',
          ls='-', lw=1)

  plt.bar(status4_, status4, width=width, color='#252525', label='Ensemble Feature', ec='black', align='center',
          ls='-', lw=1)


  # plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
  plt.margins(0,0)

  # loc='upper center', bbox_to_anchor=(0.85,0.75)
  plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.02), fontsize=14,ncol=2)
  plt.subplots_adjust(left=0.12, bottom=0.08, right=0.99, top=0.88, wspace=0.35, hspace=0.25)
  pdf.savefig()
  plt.close()
  pdf.close()
# zzz()

def zzzaa ():
  pdf = PdfPages('defence_ensemble.pdf')
  fig = plt.figure()
  # [0.76, 0.49, 0.70, 0.69]
  # [0.82, 0.0, 0.75, 0.77]
  # status1=np.array([0.13, 0.86, 0.61, 0.42])
  status1 = np.array([0.0, 0.924, 0.537, 0.112])
  status1 = status1 * 100
  # status2=np.array([0.49, 0.01])
  # status3 = np.array([0.70, 0.75])
  # status4 = np.array([0.69, 0.77])

  plt.ylim(0, 100)
  plt.xticks(fontsize=14)
  plt.yticks(fontsize=14)
  plt.ylabel('Evasion rate', fontsize=14)
  lef_space = 2
  plt.xlim(0, 13+lef_space)

  width = 1.5

  M_x = [1+lef_space, 4+lef_space, 7+lef_space, 10+lef_space]
  group_labels = ['Base', 'No Defence', 'Ensemble\nSample', 'Ensemble\nFeature']
  # group_labels = ['NO Defence', 'Ensemble Sample', 'Ensemble Feature']
  # group_labels = ['', '', '', '']
  plt.xticks(M_x, group_labels, rotation=0)
  # plt.xlabel('Feature set', fontsize=14)

  status1_ = []
  # status2_ = []
  # status3_ = []
  # status4_ = []
  status1_ = M_x
  # for x in M_x:
  #   status1_.append(x - 1.5*width)
    # status2_.append(x - 0.5*width)
    # status3_.append(x + 0.5*width)
    # status4_.append(x + 1.5*width)

  plt.bar(status1_[0], status1[0], width=width, color='#e1e1e1', label='BASE', ec='black', align='center',
          ls='-', lw=1)

  plt.bar(status1_[1], status1[1], width=width, color='#959595', label='NO Defence', ec='black', align='center',
          ls='-', lw=1)

  plt.bar(status1_[2], status1[2], width=width, color='#505050', label='Ensemble Sample', ec='black', align='center',
          ls='-', lw=1)

  plt.bar(status1_[3], status1[3], width=width, color='#252525', label='Ensemble Feature', ec='black', align='center',
          ls='-', lw=1)


  # plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
  plt.margins(0,0)

  # loc='upper center', bbox_to_anchor=(0.85,0.75)
  # plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.02), fontsize=14,ncol=2)
  plt.subplots_adjust(left=0.12, bottom=0.1, right=0.99, top=0.9, wspace=0.35, hspace=0.25)
  pdf.savefig()
  plt.close()
  pdf.close()
# zzzaa()

def zzzz ():
  pdf = PdfPages('trigger_selection.pdf')
  fig = plt.figure()
  # [0.76, 0.49, 0.70, 0.69]
  # [0.82, 0.0, 0.75, 0.77]
  status3 = np.array([1 - 0.91, 1-0.96, 1-0.98])
  status1=np.array([1-0.34, 1-0.89, 1-0.49])
  status2=np.array([1-0.93, 1-0.19, 1-0.50])

  plt.ylim(0, 1)
  plt.xticks(fontsize=14)
  plt.yticks(fontsize=14)
  plt.ylabel('Evasion Rate', fontsize=14)
  lef_space = 2
  plt.xlim(0, 20+lef_space)

  width = 1.5

  M_x = [4+lef_space-1, 15+lef_space-5-0.5, 26+lef_space-10]
  group_labels = ['SVM', 'RF', "KNN"]
  plt.xticks(M_x, group_labels, rotation=0)
  # plt.xlabel('Feature set', fontsize=14)

  status1_ = []
  status2_ = []
  status3_ = []
  for x in M_x:
    status1_.append(x - 1 * width)
    status2_.append(x)
    status3_.append(x + 1 * width)

  plt.bar(status1_, status3, width=width, color='#e1e1e1', label='Baseline', ec='black', align='center',
          ls='-', lw=1)

  plt.bar(status2_, status1, width=width, color='#505050', label='Unimportant feature', ec='black', align='center',
          ls='-', lw=1)

  plt.bar(status3_, status2, width=width, color='#959595', label='Important feature', ec='black', align='center',
          ls='-', lw=1)

  # plt.bar(status3_, status3, width=width, color='#505050', label='Ensemble Sample', ec='black', align='center',
  #         ls='-', lw=1)
  #
  # plt.bar(status4_, status4, width=width, color='#252525', label='Ensemble Feature', ec='black', align='center',
  #         ls='-', lw=1)


  # plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
  plt.margins(0,0)

  # loc='upper center', bbox_to_anchor=(0.85,0.75)
  plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.02), fontsize=14,ncol=2)
  plt.subplots_adjust(left=0.12, bottom=0.08, right=0.99, top=0.88, wspace=0.35, hspace=0.25)
  pdf.savefig()
  plt.close()
  pdf.close()
# zzzz()

def hz_bar():
  axplorer = {'android.permission.INTERNET': 2380, 'android.permission.WRITE_EXTERNAL_STORAGE': 1405, 'android.permission.VIBRATE': 737, 'android.permission.READ_EXTERNAL_STORAGE': 667, 'android.permission.RECEIVE_BOOT_COMPLETED': 509, 'android.permission.GET_ACCOUNTS': 380, 'android.permission.ACCESS_WIFI_STATE': 360, 'android.permission.READ_PHONE_STATE': 353, 'android.permission.CAMERA': 295, 'android.permission.WAKE_LOCK': 260, 'android.permission.ACCESS_FINE_LOCATION': 219, 'android.permission.ACCESS_NETWORK_STATE': 201, 'android.permission.ACCESS_COARSE_LOCATION': 185, 'android.permission.CALL_PHONE': 171, 'android.permission.RECORD_AUDIO': 154, 'android.permission.SYSTEM_ALERT_WINDOW': 138, 'android.permission.WRITE_SETTINGS': 137, 'android.permission.READ_APP_BADGE': 130, 'android.permission.READ_CONTACTS': 114, 'android.permission.WRITE_CALENDAR': 89, 'android.permission.USE_CREDENTIALS': 88, 'android.permission.READ_CALENDAR': 79, 'android.permission.MODIFY_AUDIO_SETTINGS': 71, 'android.permission.RECEIVE_USER_PRESENT': 62, 'android.permission.FLASHLIGHT': 57, 'android.permission.CHANGE_NETWORK_STATE': 54, 'android.permission.CHANGE_WIFI_STATE': 52, 'android.permission.MANAGE_ACCOUNTS': 45}
  arcade = {'android.permission.INTERNET': 2380, 'android.permission.ACCESS_NETWORK_STATE': 2246, 'android.permission.WAKE_LOCK': 1546, 'android.permission.WRITE_EXTERNAL_STORAGE': 1405, 'android.permission.ACCESS_WIFI_STATE': 759, 'android.permission.VIBRATE': 737, 'android.permission.READ_EXTERNAL_STORAGE': 682, 'android.permission.ACCESS_FINE_LOCATION': 589, 'android.permission.ACCESS_COARSE_LOCATION': 530, 'android.permission.RECEIVE_BOOT_COMPLETED': 525, 'android.permission.READ_PHONE_STATE': 515, 'android.permission.GET_ACCOUNTS': 380, 'android.permission.CAMERA': 295, 'android.permission.CALL_PHONE': 171, 'android.permission.RECORD_AUDIO': 154, 'android.permission.BLUETOOTH': 150, 'android.permission.SYSTEM_ALERT_WINDOW': 138, 'android.permission.WRITE_SETTINGS': 137, 'android.permission.READ_APP_BADGE': 130, 'android.permission.GET_TASKS': 124, 'android.permission.CHANGE_WIFI_STATE': 124, 'android.permission.READ_CONTACTS': 114, 'android.permission.BLUETOOTH_ADMIN': 107, 'android.permission.MODIFY_AUDIO_SETTINGS': 91, 'android.permission.WRITE_CALENDAR': 89, 'android.permission.USE_CREDENTIALS': 88, 'android.permission.READ_CALENDAR': 79, 'android.permission.RECEIVE_USER_PRESENT': 62, 'android.permission.FLASHLIGHT': 57, 'android.permission.SET_WALLPAPER': 57, 'android.permission.CHANGE_NETWORK_STATE': 57, 'android.permission.SEND_SMS': 53, 'android.permission.MANAGE_ACCOUNTS': 45, 'android.permission.WRITE_CONTACTS': 45, 'android.permission.DISABLE_KEYGUARD': 42, 'android.permission.AUTHENTICATE_ACCOUNTS': 40, 'android.permission.USE_FINGERPRINT': 38, 'android.permission.MOUNT_UNMOUNT_FILESYSTEMS': 32}
  our_axplorer= {'android.permission.INTERNET': 1498, 'android.permission.WRITE_EXTERNAL_STORAGE': 1405, 'android.permission.VIBRATE': 737, 'android.permission.READ_EXTERNAL_STORAGE': 667, 'android.permission.RECEIVE_BOOT_COMPLETED': 509, 'android.permission.GET_ACCOUNTS': 380, 'android.permission.ACCESS_WIFI_STATE': 360, 'android.permission.READ_PHONE_STATE': 353, 'android.permission.CAMERA': 277, 'android.permission.WAKE_LOCK': 260, 'android.permission.ACCESS_FINE_LOCATION': 219, 'android.permission.ACCESS_NETWORK_STATE': 201, 'android.permission.ACCESS_COARSE_LOCATION': 185, 'android.permission.CALL_PHONE': 171, 'android.permission.SYSTEM_ALERT_WINDOW': 138, 'android.permission.WRITE_SETTINGS': 137, 'android.permission.READ_APP_BADGE': 130, 'android.permission.READ_CONTACTS': 114, 'android.permission.WRITE_CALENDAR': 89, 'android.permission.USE_CREDENTIALS': 88, 'android.permission.READ_CALENDAR': 79, 'android.permission.RECEIVE_USER_PRESENT': 62, 'android.permission.FLASHLIGHT': 57, 'android.permission.CHANGE_NETWORK_STATE': 54, 'android.permission.CHANGE_WIFI_STATE': 52, 'android.permission.MANAGE_ACCOUNTS': 45, 'android.permission.WRITE_CONTACTS': 45, 'android.permission.AUTHENTICATE_ACCOUNTS': 40, 'android.permission.BLUETOOTH': 34, 'android.permission.DISABLE_KEYGUARD': 32, 'android.permission.MOUNT_UNMOUNT_FILESYSTEMS': 32}
  our_arcade = {'android.permission.ACCESS_NETWORK_STATE': 2246, 'android.permission.WAKE_LOCK': 1546, 'android.permission.INTERNET': 1498, 'android.permission.WRITE_EXTERNAL_STORAGE': 1405, 'android.permission.ACCESS_WIFI_STATE': 759, 'android.permission.VIBRATE': 737, 'android.permission.READ_EXTERNAL_STORAGE': 682, 'android.permission.ACCESS_FINE_LOCATION': 589, 'android.permission.ACCESS_COARSE_LOCATION': 530, 'android.permission.RECEIVE_BOOT_COMPLETED': 525, 'android.permission.READ_PHONE_STATE': 515, 'android.permission.GET_ACCOUNTS': 380, 'android.permission.CAMERA': 277, 'android.permission.CALL_PHONE': 171, 'android.permission.BLUETOOTH': 150, 'android.permission.SYSTEM_ALERT_WINDOW': 138, 'android.permission.WRITE_SETTINGS': 137, 'android.permission.READ_APP_BADGE': 130, 'android.permission.GET_TASKS': 124, 'android.permission.CHANGE_WIFI_STATE': 124, 'android.permission.READ_CONTACTS': 114, 'android.permission.BLUETOOTH_ADMIN': 107, 'android.permission.WRITE_CALENDAR': 89, 'android.permission.USE_CREDENTIALS': 88, 'android.permission.READ_CALENDAR': 79, 'android.permission.RECEIVE_USER_PRESENT': 62, 'android.permission.FLASHLIGHT': 57, 'android.permission.SET_WALLPAPER': 57, 'android.permission.CHANGE_NETWORK_STATE': 57, 'android.permission.SEND_SMS': 53, 'android.permission.MANAGE_ACCOUNTS': 45, 'android.permission.WRITE_CONTACTS': 45, 'android.permission.DISABLE_KEYGUARD': 42, 'android.permission.AUTHENTICATE_ACCOUNTS': 40, 'android.permission.USE_FINGERPRINT': 38, 'android.permission.MOUNT_UNMOUNT_FILESYSTEMS': 32}

  category = []
  axplorer_date = []
  arcade_date = []
  our_axplorer_date = []
  our_arcade_date = []

  for i, k in enumerate(axplorer.keys()):
    if i>=10:
      break
    category.append(k)

    axplorer_date.append(axplorer[k])
    arcade_date.append(arcade[k])
    our_axplorer_date.append(our_axplorer[k])
    our_arcade_date.append(our_arcade[k])

  category.reverse()
  axplorer_date.reverse()
  arcade_date.reverse()
  our_axplorer_date.reverse()
  our_arcade_date.reverse()

  total_height = 0.8
  n_bar = 4  # 做双柱状图，所以n=2
  height = total_height / n_bar

  x = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
  plt_axplorer_date = plt.barh(x, axplorer_date, height=-height, color='m', label='Axplorer', fc='y')

  # 设定尺寸
  pdf = PdfPages('unneeded_permission_over_privilege.pdf')
  fig = plt.gcf()
  fig.set_size_inches(8, 8)
  plt.grid(axis='x', which='major')
  # plt.rc('axes', axisbelow=True)

  # plt.title('Top 10 Google Play Store Applications Unneeded Permissions', fontsize=17, fontweight="bold")

  # 紧挨着第一个柱条plot第二条柱，这一步是比较tricky的地方
  for i in range(len(x)):
    x[i] = x[i] + height
  plt_arcade_date = plt.barh(x, arcade_date, height=height, label='Arcade', color='deepskyblue', tick_label=category, align='center')

  # 紧挨着第一个柱条plot第二条柱，这一步是比较tricky的地方
  for i in range(len(x)):
    x[i] = x[i] + height
  plt_our_axplorer_date = plt.barh(x, our_axplorer_date, height=height, label='NatiDroid + Axplorer', color='palegreen', tick_label=category, align='center')

  # 紧挨着第一个柱条plot第二条柱，这一步是比较tricky的地方
  for i in range(len(x)):
    x[i] = x[i] + height
  plt_our_arcade_date6 = plt.barh(x, our_arcade_date, height=height, label='NatiDroid + Arcade', color='orangered', tick_label=category, align='center')

  ax = plt.gca()
  ax.legend(["Axplorer", "Arcade", "NatiDroid + Axplorer", "NatiDroid + Arcade"], prop={'size': 10})  # 设置图例
  ax.spines['top'].set_visible(False)  # 去掉上边框
  ax.spines['right'].set_visible(False)  # 去掉右边框
  ax.set_yticklabels(category, fontsize=9)
  ax.set_axisbelow(True)
  plt.xlabel('# of Unneeded Permissions', fontsize=10)

  plt.subplots_adjust(left=0.54, bottom=0.06, right=0.96, top=0.99, wspace=0.35, hspace=0.25)

  # plt.show()
  pdf.savefig()
  plt.close()
  pdf.close()
# hz_bar()


def bar():
  axplorer = {'android.permission.INTERNET': 2380, 'android.permission.WRITE_EXTERNAL_STORAGE': 1405, 'android.permission.VIBRATE': 737, 'android.permission.READ_EXTERNAL_STORAGE': 667, 'android.permission.RECEIVE_BOOT_COMPLETED': 509, 'android.permission.GET_ACCOUNTS': 380, 'android.permission.ACCESS_WIFI_STATE': 360, 'android.permission.READ_PHONE_STATE': 353, 'android.permission.CAMERA': 295, 'android.permission.WAKE_LOCK': 260, 'android.permission.ACCESS_FINE_LOCATION': 219, 'android.permission.ACCESS_NETWORK_STATE': 201, 'android.permission.ACCESS_COARSE_LOCATION': 185, 'android.permission.CALL_PHONE': 171, 'android.permission.RECORD_AUDIO': 154, 'android.permission.SYSTEM_ALERT_WINDOW': 138, 'android.permission.WRITE_SETTINGS': 137, 'android.permission.READ_APP_BADGE': 130, 'android.permission.READ_CONTACTS': 114, 'android.permission.WRITE_CALENDAR': 89, 'android.permission.USE_CREDENTIALS': 88, 'android.permission.READ_CALENDAR': 79, 'android.permission.MODIFY_AUDIO_SETTINGS': 71, 'android.permission.RECEIVE_USER_PRESENT': 62, 'android.permission.FLASHLIGHT': 57, 'android.permission.CHANGE_NETWORK_STATE': 54, 'android.permission.CHANGE_WIFI_STATE': 52, 'android.permission.MANAGE_ACCOUNTS': 45}
  arcade = {'android.permission.INTERNET': 2380, 'android.permission.ACCESS_NETWORK_STATE': 2246, 'android.permission.WAKE_LOCK': 1546, 'android.permission.WRITE_EXTERNAL_STORAGE': 1405, 'android.permission.ACCESS_WIFI_STATE': 759, 'android.permission.VIBRATE': 737, 'android.permission.READ_EXTERNAL_STORAGE': 682, 'android.permission.ACCESS_FINE_LOCATION': 589, 'android.permission.ACCESS_COARSE_LOCATION': 530, 'android.permission.RECEIVE_BOOT_COMPLETED': 525, 'android.permission.READ_PHONE_STATE': 515, 'android.permission.GET_ACCOUNTS': 380, 'android.permission.CAMERA': 295, 'android.permission.CALL_PHONE': 171, 'android.permission.RECORD_AUDIO': 154, 'android.permission.BLUETOOTH': 150, 'android.permission.SYSTEM_ALERT_WINDOW': 138, 'android.permission.WRITE_SETTINGS': 137, 'android.permission.READ_APP_BADGE': 130, 'android.permission.GET_TASKS': 124, 'android.permission.CHANGE_WIFI_STATE': 124, 'android.permission.READ_CONTACTS': 114, 'android.permission.BLUETOOTH_ADMIN': 107, 'android.permission.MODIFY_AUDIO_SETTINGS': 91, 'android.permission.WRITE_CALENDAR': 89, 'android.permission.USE_CREDENTIALS': 88, 'android.permission.READ_CALENDAR': 79, 'android.permission.RECEIVE_USER_PRESENT': 62, 'android.permission.FLASHLIGHT': 57, 'android.permission.SET_WALLPAPER': 57, 'android.permission.CHANGE_NETWORK_STATE': 57, 'android.permission.SEND_SMS': 53, 'android.permission.MANAGE_ACCOUNTS': 45, 'android.permission.WRITE_CONTACTS': 45, 'android.permission.DISABLE_KEYGUARD': 42, 'android.permission.AUTHENTICATE_ACCOUNTS': 40, 'android.permission.USE_FINGERPRINT': 38, 'android.permission.MOUNT_UNMOUNT_FILESYSTEMS': 32}
  our_axplorer= {'android.permission.INTERNET': 1498, 'android.permission.WRITE_EXTERNAL_STORAGE': 1405, 'android.permission.VIBRATE': 737, 'android.permission.READ_EXTERNAL_STORAGE': 667, 'android.permission.RECEIVE_BOOT_COMPLETED': 509, 'android.permission.GET_ACCOUNTS': 380, 'android.permission.ACCESS_WIFI_STATE': 360, 'android.permission.READ_PHONE_STATE': 353, 'android.permission.CAMERA': 277, 'android.permission.WAKE_LOCK': 260, 'android.permission.ACCESS_FINE_LOCATION': 219, 'android.permission.ACCESS_NETWORK_STATE': 201, 'android.permission.ACCESS_COARSE_LOCATION': 185, 'android.permission.CALL_PHONE': 171, 'android.permission.SYSTEM_ALERT_WINDOW': 138, 'android.permission.WRITE_SETTINGS': 137, 'android.permission.READ_APP_BADGE': 130, 'android.permission.READ_CONTACTS': 114, 'android.permission.WRITE_CALENDAR': 89, 'android.permission.USE_CREDENTIALS': 88, 'android.permission.READ_CALENDAR': 79, 'android.permission.RECEIVE_USER_PRESENT': 62, 'android.permission.FLASHLIGHT': 57, 'android.permission.CHANGE_NETWORK_STATE': 54, 'android.permission.CHANGE_WIFI_STATE': 52, 'android.permission.MANAGE_ACCOUNTS': 45, 'android.permission.WRITE_CONTACTS': 45, 'android.permission.AUTHENTICATE_ACCOUNTS': 40, 'android.permission.BLUETOOTH': 34, 'android.permission.DISABLE_KEYGUARD': 32, 'android.permission.MOUNT_UNMOUNT_FILESYSTEMS': 32}
  our_arcade = {'android.permission.ACCESS_NETWORK_STATE': 2246, 'android.permission.WAKE_LOCK': 1546, 'android.permission.INTERNET': 1498, 'android.permission.WRITE_EXTERNAL_STORAGE': 1405, 'android.permission.ACCESS_WIFI_STATE': 759, 'android.permission.VIBRATE': 737, 'android.permission.READ_EXTERNAL_STORAGE': 682, 'android.permission.ACCESS_FINE_LOCATION': 589, 'android.permission.ACCESS_COARSE_LOCATION': 530, 'android.permission.RECEIVE_BOOT_COMPLETED': 525, 'android.permission.READ_PHONE_STATE': 515, 'android.permission.GET_ACCOUNTS': 380, 'android.permission.CAMERA': 277, 'android.permission.CALL_PHONE': 171, 'android.permission.BLUETOOTH': 150, 'android.permission.SYSTEM_ALERT_WINDOW': 138, 'android.permission.WRITE_SETTINGS': 137, 'android.permission.READ_APP_BADGE': 130, 'android.permission.GET_TASKS': 124, 'android.permission.CHANGE_WIFI_STATE': 124, 'android.permission.READ_CONTACTS': 114, 'android.permission.BLUETOOTH_ADMIN': 107, 'android.permission.WRITE_CALENDAR': 89, 'android.permission.USE_CREDENTIALS': 88, 'android.permission.READ_CALENDAR': 79, 'android.permission.RECEIVE_USER_PRESENT': 62, 'android.permission.FLASHLIGHT': 57, 'android.permission.SET_WALLPAPER': 57, 'android.permission.CHANGE_NETWORK_STATE': 57, 'android.permission.SEND_SMS': 53, 'android.permission.MANAGE_ACCOUNTS': 45, 'android.permission.WRITE_CONTACTS': 45, 'android.permission.DISABLE_KEYGUARD': 42, 'android.permission.AUTHENTICATE_ACCOUNTS': 40, 'android.permission.USE_FINGERPRINT': 38, 'android.permission.MOUNT_UNMOUNT_FILESYSTEMS': 32}

  category = []
  axplorer_date = []
  arcade_date = []
  our_axplorer_date = []
  our_arcade_date = []

  for i, k in enumerate(axplorer.keys()):
    if i>=10:
      break
    category.append(k.replace('android.permission.',''))

    axplorer_date.append(axplorer[k])
    arcade_date.append(arcade[k])
    our_axplorer_date.append(our_axplorer[k])
    our_arcade_date.append(our_arcade[k])

  # category.reverse()
  # axplorer_date.reverse()
  # arcade_date.reverse()
  # our_axplorer_date.reverse()
  # our_arcade_date.reverse()

  total_height = 0.8
  n_bar = 4  # 做双柱状图，所以n=2
  height = total_height / n_bar

  x = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
  print(x)
  plt_axplorer_date = plt.bar(x, axplorer_date, width=-height, color='#e78b82', label='Axplorer', fc='y')

  # 设定尺寸
  pdf = PdfPages('unneeded_permission_over_privilege_hz.pdf')
  fig = plt.gcf()
  fig.set_size_inches(8, 3)
  plt.grid(axis='y', which='major')
  # plt.rc('axes', axisbelow=True)

  # 紧挨着第一个柱条plot第二条柱，这一步是比较tricky的地方
  for i in range(len(x)):
    x[i] = x[i] + height
  print(x)
  plt_arcade_date = plt.bar(x, arcade_date, width=height, label='Arcade', color='#c4d6a0', align='center')

  # 紧挨着第一个柱条plot第二条柱，这一步是比较tricky的地方
  for i in range(len(x)):
    x[i] = x[i] + height
  print(x)
  plt_our_axplorer_date = plt.bar(x, our_axplorer_date, width=height, label='NatiDroid + Axplorer', color='#dc8647', align='center')

  # 紧挨着第一个柱条plot第二条柱，这一步是比较tricky的地方
  for i in range(len(x)):
    x[i] = x[i] + height
  print(x)
  plt_our_arcade_date6 = plt.bar(x, our_arcade_date, width=height, label='NatiDroid + Arcade', color='#eeeaf2', align='center')

  ax = plt.gca()
  ax.legend(["Axplorer", "Arcade", "NatiDroid + Axplorer", "NatiDroid + Arcade"], prop={'size': 10})  # 设置图例
  ax.spines['top'].set_visible(False)  # 去掉上边框
  ax.spines['right'].set_visible(False)  # 去掉右边框
  ax.set_axisbelow(True)
  plt.ylabel('# of Unneeded Permissions', fontsize=9)
  plt.xlabel('Permission Name', fontsize=9)
  for i in range(len(x)):
    x[i] = x[i] - height * 2 + 1/2 * height
  print('===', x)
  ax.set_xticks(x)
  ax.set_xticklabels(category, rotation=17, fontsize=6)
  plt.subplots_adjust(left=0.12, bottom=0.23, right=0.99, top=0.92, wspace=0.35, hspace=0.25)

  pdf.savefig()
  plt.close()
  pdf.close()
bar()