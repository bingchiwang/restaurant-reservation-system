import React, { useState, useEffect, useCallback } from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
  ActivityIndicator
} from 'react-native';
import { useAuth } from '../context/AuthContext';
import { MemberAPI, ReservationAPI } from '../api/client';

export default function MemberScreen() {
  const { token, user, isLoggedIn, login, register, logout, updateProfile } = useAuth();

  // Login / Register state
  const [authMode, setAuthMode] = useState('login'); // 'login' | 'register'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Member Dashboard state
  const [historyTab, setHistoryTab] = useState('reservations'); // 'reservations' | 'orders'
  const [reservations, setReservations] = useState([]);
  const [orders, setOrders] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Profile Edit state
  const [editingName, setEditingName] = useState(false);
  const [newName, setNewName] = useState('');

  const loadHistory = useCallback(async () => {
    if (!token || !isLoggedIn) return;
    setLoadingHistory(true);
    try {
      const [resList, ordList] = await Promise.all([
        MemberAPI.getMyReservations(token),
        MemberAPI.getMyOrders(token)
      ]);
      if (resList.success) setReservations(resList.data || []);
      if (ordList.success) setOrders(ordList.data || []);
    } catch (err) {
      console.warn('載入會員紀錄失敗', err);
    } finally {
      setLoadingHistory(false);
    }
  }, [token, isLoggedIn]);

  useEffect(() => {
    if (isLoggedIn) {
      loadHistory();
    }
  }, [isLoggedIn, loadHistory]);

  const handleAuthSubmit = async () => {
    if (!email.trim() || !password) {
      Alert.alert('請填寫完整資訊', '請輸入電子郵件與密碼');
      return;
    }
    if (authMode === 'register' && !displayName.trim()) {
      Alert.alert('請填寫暱稱', '請輸入顯示名稱');
      return;
    }

    setSubmitting(true);
    try {
      if (authMode === 'login') {
        await login(email.trim(), password);
      } else {
        await register(email.trim(), password, displayName.trim());
        Alert.alert('註冊成功', '已為您自動登入會員帳號！');
      }
      setPassword('');
    } catch (err) {
      Alert.alert(authMode === 'login' ? '登入失敗' : '註冊失敗', err.message || '請檢查輸入資料');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSaveName = async () => {
    if (!newName.trim()) {
      Alert.alert('名稱不可為空', '請輸入有效顯示名稱');
      return;
    }
    try {
      await updateProfile({ display_name: newName.trim() });
      setEditingName(false);
      Alert.alert('更新成功', '會員暱稱已更新');
    } catch (err) {
      Alert.alert('更新失敗', err.message);
    }
  };

  const handleCancelReservation = (reservationCode) => {
    Alert.alert(
      '確認取消預約',
      `確定要取消預約 ${reservationCode} 並釋放桌位嗎？`,
      [
        { text: '保留', style: 'cancel' },
        {
          text: '確定取消',
          style: 'destructive',
          onPress: async () => {
            try {
              const res = await ReservationAPI.cancelReservation(reservationCode, null, token);
              if (res.success) {
                Alert.alert('取消成功', '已取消該筆預約並釋放桌位');
                loadHistory();
              }
            } catch (err) {
              Alert.alert('取消失敗', err.message || '無法取消此預約');
            }
          }
        }
      ]
    );
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'CONFIRMED':
      case 'READY':
        return '#2a9d8f';
      case 'PREPARING':
        return '#e76f51';
      case 'COMPLETED':
        return '#457b9d';
      case 'CANCELLED':
        return '#e63946';
      default:
        return '#e9a825';
    }
  };

  if (!isLoggedIn) {
    return (
      <ScrollView style={styles.container} contentContainerStyle={styles.authContent}>
        <View style={styles.authCard}>
          <Text style={styles.authTitle}>
            {authMode === 'login' ? '👤 顧客會員登入' : '✨ 註冊新會員'}
          </Text>
          <Text style={styles.authSubtitle}>
            訪客免登入仍可預約與點餐；登入會員可自動保存與查看您的專屬預約與訂單紀錄。
          </Text>

          {/* Mode Toggle */}
          <View style={styles.modeSwitch}>
            <TouchableOpacity
              style={[styles.modeBtn, authMode === 'login' && styles.modeBtnActive]}
              onPress={() => setAuthMode('login')}
            >
              <Text style={[styles.modeBtnText, authMode === 'login' && styles.modeBtnTextActive]}>
                會員登入
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.modeBtn, authMode === 'register' && styles.modeBtnActive]}
              onPress={() => setAuthMode('register')}
            >
              <Text style={[styles.modeBtnText, authMode === 'register' && styles.modeBtnTextActive]}>
                註冊會員
              </Text>
            </TouchableOpacity>
          </View>

          {authMode === 'register' && (
            <View style={styles.inputGroup}>
              <Text style={styles.label}>顯示名稱 / 姓名 *</Text>
              <TextInput
                style={styles.input}
                placeholder="例：王小明"
                value={displayName}
                onChangeText={setDisplayName}
              />
            </View>
          )}

          <View style={styles.inputGroup}>
            <Text style={styles.label}>電子郵件 (Email) *</Text>
            <TextInput
              style={styles.input}
              placeholder="example@email.com"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>密碼 {authMode === 'register' ? '(至少 6 碼) *' : '*'}</Text>
            <TextInput
              style={styles.input}
              placeholder="請輸入密碼"
              value={password}
              onChangeText={setPassword}
              secureTextEntry
            />
          </View>

          <TouchableOpacity
            style={[styles.submitBtn, submitting && styles.disabledBtn]}
            onPress={handleAuthSubmit}
            disabled={submitting}
          >
            {submitting ? (
              <ActivityIndicator color="#ffffff" />
            ) : (
              <Text style={styles.submitBtnText}>
                {authMode === 'login' ? '登入會員' : '建立會員帳號'}
              </Text>
            )}
          </TouchableOpacity>
        </View>
      </ScrollView>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.dashboardContent}>
      {/* Member Profile Card */}
      <View style={styles.profileCard}>
        <View style={styles.profileTop}>
          <View style={{ flex: 1 }}>
            <Text style={styles.profileGreeting}>👤 {user.display_name}</Text>
            <Text style={styles.profileEmail}>{user.email}</Text>
          </View>
          <TouchableOpacity style={styles.logoutBtn} onPress={logout}>
            <Text style={styles.logoutBtnText}>登出</Text>
          </TouchableOpacity>
        </View>

        {editingName ? (
          <View style={styles.editNameRow}>
            <TextInput
              style={[styles.input, { flex: 1, marginBottom: 0 }]}
              value={newName}
              onChangeText={setNewName}
              placeholder="輸入新名稱"
            />
            <TouchableOpacity style={styles.saveNameBtn} onPress={handleSaveName}>
              <Text style={styles.saveNameBtnText}>儲存</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.cancelEditBtn} onPress={() => setEditingName(false)}>
              <Text style={styles.cancelEditText}>取消</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <TouchableOpacity
            style={styles.editProfileLink}
            onPress={() => {
              setNewName(user.display_name);
              setEditingName(true);
            }}
          >
            <Text style={styles.editProfileLinkText}>✏️ 修改顯示名稱</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Sub-tabs: My Reservations vs My Orders */}
      <View style={styles.historyHeader}>
        <View style={styles.historyTabs}>
          <TouchableOpacity
            style={[styles.historyTab, historyTab === 'reservations' && styles.historyTabActive]}
            onPress={() => setHistoryTab('reservations')}
          >
            <Text style={[styles.historyTabText, historyTab === 'reservations' && styles.historyTabTextActive]}>
              📅 我的預約 ({reservations.length})
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.historyTab, historyTab === 'orders' && styles.historyTabActive]}
            onPress={() => setHistoryTab('orders')}
          >
            <Text style={[styles.historyTabText, historyTab === 'orders' && styles.historyTabTextActive]}>
              🧾 我的訂單 ({orders.length})
            </Text>
          </TouchableOpacity>
        </View>
        <TouchableOpacity style={styles.refreshBtn} onPress={loadHistory}>
          <Text style={styles.refreshBtnText}>🔄</Text>
        </TouchableOpacity>
      </View>

      {loadingHistory ? (
        <View style={styles.centerBox}>
          <ActivityIndicator size="large" color="#1d3557" />
        </View>
      ) : historyTab === 'reservations' ? (
        reservations.length === 0 ? (
          <View style={styles.centerBox}>
            <Text style={styles.emptyText}>尚無預約紀錄，歡迎前往「線上預約」訂位！</Text>
          </View>
        ) : (
          reservations.map((r) => (
            <View key={r.reservation_id} style={styles.recordCard}>
              <View style={styles.recordHeader}>
                <Text style={styles.recordCode}>{r.reservation_code}</Text>
                <View style={[styles.badge, { backgroundColor: getStatusColor(r.status) }]}>
                  <Text style={styles.badgeText}>{r.status}</Text>
                </View>
              </View>
              <Text style={styles.recordLine}>📅 用餐時間：{r.start_at}</Text>
              <Text style={styles.recordLine}>
                👥 人數與桌位：{r.party_size} 位 / {r.table_name || `桌號 #${r.table_id}`}
              </Text>
              {r.status === 'CONFIRMED' && (
                <TouchableOpacity
                  style={styles.cancelResBtn}
                  onPress={() => handleCancelReservation(r.reservation_code)}
                >
                  <Text style={styles.cancelResText}>取消預約並釋放桌位</Text>
                </TouchableOpacity>
              )}
            </View>
          ))
        )
      ) : orders.length === 0 ? (
        <View style={styles.centerBox}>
          <Text style={styles.emptyText}>尚無點餐紀錄，快去看看美味菜單吧！</Text>
        </View>
      ) : (
        orders.map((o) => (
          <View key={o.order_id} style={styles.recordCard}>
            <View style={styles.recordHeader}>
              <Text style={styles.recordCode}>
                訂單 #{o.order_id} ({o.order_type === 'PRE_ORDER' ? '預約預點' : '現場點餐'})
              </Text>
              <View style={[styles.badge, { backgroundColor: getStatusColor(o.status) }]}>
                <Text style={styles.badgeText}>{o.status}</Text>
              </View>
            </View>
            <Text style={styles.recordLine}>
              🪑 桌位：{o.table_name || (o.table_id ? `#${o.table_id}` : '未指定')}
            </Text>
            <Text style={styles.recordLine}>🕒 下單時間：{o.created_at}</Text>
            <Text style={styles.recordPrice}>💰 總金額：NT$ {o.total_amount}</Text>

            {o.items && o.items.length > 0 && (
              <View style={styles.orderItemsBox}>
                {o.items.map((it) => (
                  <Text key={it.order_item_id} style={styles.orderItemText}>
                    • {it.item_name_snapshot} × {it.quantity} — NT$ {it.subtotal}
                  </Text>
                ))}
              </View>
            )}
          </View>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  authContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
  },
  authCard: {
    backgroundColor: '#ffffff',
    borderRadius: 14,
    padding: 24,
    shadowColor: '#000',
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  authTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1d3557',
    textAlign: 'center',
  },
  authSubtitle: {
    fontSize: 13,
    color: '#6c757d',
    textAlign: 'center',
    marginTop: 6,
    marginBottom: 18,
    lineHeight: 19,
  },
  modeSwitch: {
    flexDirection: 'row',
    backgroundColor: '#e9ecef',
    borderRadius: 8,
    padding: 4,
    marginBottom: 16,
  },
  modeBtn: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 6,
  },
  modeBtnActive: {
    backgroundColor: '#ffffff',
  },
  modeBtnText: {
    fontSize: 14,
    color: '#6c757d',
    fontWeight: '600',
  },
  modeBtnTextActive: {
    color: '#1d3557',
    fontWeight: 'bold',
  },
  inputGroup: {
    marginBottom: 12,
  },
  label: {
    fontSize: 13,
    fontWeight: '600',
    color: '#495057',
    marginBottom: 6,
  },
  input: {
    backgroundColor: '#f8f9fa',
    borderWidth: 1,
    borderColor: '#ced4da',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 15,
  },
  submitBtn: {
    backgroundColor: '#e63946',
    borderRadius: 10,
    paddingVertical: 13,
    alignItems: 'center',
    marginTop: 8,
  },
  submitBtnText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  disabledBtn: {
    opacity: 0.6,
  },
  dashboardContent: {
    padding: 16,
    paddingBottom: 32,
  },
  profileCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  profileTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  profileGreeting: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1d3557',
  },
  profileEmail: {
    fontSize: 13,
    color: '#6c757d',
    marginTop: 2,
  },
  logoutBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#f1f3f5',
    borderRadius: 6,
  },
  logoutBtnText: {
    fontSize: 13,
    color: '#e63946',
    fontWeight: 'bold',
  },
  editProfileLink: {
    marginTop: 10,
    alignSelf: 'flex-start',
  },
  editProfileLinkText: {
    fontSize: 13,
    color: '#457b9d',
    fontWeight: '600',
  },
  editNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 12,
  },
  saveNameBtn: {
    backgroundColor: '#2a9d8f',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 8,
  },
  saveNameBtnText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: 'bold',
  },
  cancelEditBtn: {
    paddingHorizontal: 10,
    paddingVertical: 10,
  },
  cancelEditText: {
    color: '#6c757d',
    fontSize: 13,
  },
  historyHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  historyTabs: {
    flex: 1,
    flexDirection: 'row',
    backgroundColor: '#e9ecef',
    borderRadius: 8,
    padding: 4,
  },
  historyTab: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 6,
  },
  historyTabActive: {
    backgroundColor: '#ffffff',
  },
  historyTabText: {
    fontSize: 13,
    color: '#6c757d',
    fontWeight: '600',
  },
  historyTabTextActive: {
    color: '#1d3557',
    fontWeight: 'bold',
  },
  refreshBtn: {
    padding: 8,
    backgroundColor: '#ffffff',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#dee2e6',
  },
  refreshBtnText: {
    fontSize: 16,
  },
  centerBox: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 14,
    color: '#adb5bd',
  },
  recordCard: {
    backgroundColor: '#ffffff',
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  recordHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#f1f3f5',
    paddingBottom: 8,
    marginBottom: 8,
  },
  recordCode: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1d3557',
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 5,
  },
  badgeText: {
    color: '#ffffff',
    fontSize: 11,
    fontWeight: 'bold',
  },
  recordLine: {
    fontSize: 13,
    color: '#495057',
    marginBottom: 4,
  },
  recordPrice: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#e63946',
    marginTop: 2,
  },
  orderItemsBox: {
    backgroundColor: '#f8f9fa',
    borderRadius: 6,
    padding: 8,
    marginTop: 8,
  },
  orderItemText: {
    fontSize: 12,
    color: '#495057',
    marginBottom: 2,
  },
  cancelResBtn: {
    marginTop: 8,
    paddingVertical: 8,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#e63946',
    alignItems: 'center',
  },
  cancelResText: {
    color: '#e63946',
    fontSize: 13,
    fontWeight: 'bold',
  },
});
