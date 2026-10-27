import React, { useState } from 'react';
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
import { ReservationAPI } from '../api/client';

export default function ReservationLookupScreen() {
  const [code, setCode] = useState('');
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [reservation, setReservation] = useState(null);

  const handleSearch = async () => {
    if (!code.trim() || !phone.trim()) {
      Alert.alert('請輸入完整資訊', '請輸入預約編號與登記之聯絡電話以進行身分核對');
      return;
    }

    setLoading(true);
    try {
      const res = await ReservationAPI.getReservation(code.trim(), phone.trim());
      if (res.success) {
        setReservation(res.data);
      }
    } catch (err) {
      Alert.alert('查無預約', err.message || '預約編號或聯絡電話不相符');
      setReservation(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelReservation = () => {
    Alert.alert(
      '確認取消預約',
      '取消後將釋放該桌位時段給其他顧客，確定要取消嗎？',
      [
        { text: '保留預約', style: 'cancel' },
        {
          text: '確定取消',
          style: 'destructive',
          onPress: async () => {
            setCancelling(true);
            try {
              const res = await ReservationAPI.cancelReservation(code.trim(), phone.trim());
              if (res.success) {
                Alert.alert('取消成功', '您的預約已成功取消並釋放桌位');
                setReservation(res.data);
              }
            } catch (err) {
              Alert.alert('取消失敗', err.message || '距離用餐時間不足 1 小時或系統處理異常');
            } finally {
              setCancelling(false);
            }
          }
        }
      ]
    );
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'CONFIRMED': return '#2a9d8f';
      case 'COMPLETED': return '#457b9d';
      case 'CANCELLED': return '#e63946';
      default: return '#6c757d';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'CONFIRMED': return '已確認有效';
      case 'COMPLETED': return '已完成用餐';
      case 'CANCELLED': return '已取消';
      default: return status;
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Search Form */}
      <View style={styles.searchCard}>
        <Text style={styles.searchTitle}>查詢預約紀錄</Text>
        <Text style={styles.searchSubtitle}>請輸入預約時取得之預約編號與電話進行核驗</Text>

        <TextInput
          style={styles.input}
          placeholder="預約編號 (例: RES-20261028-XXXX)"
          value={code}
          onChangeText={setCode}
          autoCapitalize="characters"
        />
        <TextInput
          style={styles.input}
          placeholder="聯絡電話 (例: 0912345678)"
          value={phone}
          onChangeText={setPhone}
          keyboardType="phone-pad"
        />

        <TouchableOpacity style={styles.searchBtn} onPress={handleSearch} disabled={loading}>
          {loading ? (
            <ActivityIndicator color="#ffffff" />
          ) : (
            <Text style={styles.searchBtnText}>查詢預約 ➔</Text>
          )}
        </TouchableOpacity>
      </View>

      {/* Reservation Details Result */}
      {reservation && (
        <View style={styles.resultCard}>
          <View style={styles.resultHeader}>
            <Text style={styles.resCodeText}>{reservation.reservation_code}</Text>
            <View style={[styles.statusBadge, { backgroundColor: getStatusColor(reservation.status) }]}>
              <Text style={styles.statusBadgeText}>{getStatusLabel(reservation.status)}</Text>
            </View>
          </View>

          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>預約姓名</Text>
            <Text style={styles.infoValue}>{reservation.guest_name}</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>聯絡電話</Text>
            <Text style={styles.infoValue}>{reservation.guest_phone}</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>用餐時段</Text>
            <Text style={styles.infoValue}>{reservation.start_at}</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>預約人數</Text>
            <Text style={styles.infoValue}>{reservation.party_size} 人</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>分配桌號</Text>
            <Text style={[styles.infoValue, { color: '#1d3557', fontWeight: 'bold' }]}>
              {reservation.table_name || `桌號 #${reservation.table_id}`}
            </Text>
          </View>

          {/* Cancel Button if eligible */}
          {reservation.status === 'CONFIRMED' && (
            <TouchableOpacity
              style={[styles.cancelBtn, cancelling && styles.disabledBtn]}
              onPress={handleCancelReservation}
              disabled={cancelling}
            >
              {cancelling ? (
                <ActivityIndicator color="#e63946" />
              ) : (
                <Text style={styles.cancelBtnText}>取消此筆預約 (釋放座位)</Text>
              )}
            </TouchableOpacity>
          )}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  content: {
    padding: 20,
  },
  searchCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 2,
  },
  searchTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1d3557',
  },
  searchSubtitle: {
    fontSize: 13,
    color: '#6c757d',
    marginTop: 4,
    marginBottom: 16,
  },
  input: {
    backgroundColor: '#f8f9fa',
    borderWidth: 1,
    borderColor: '#ced4da',
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10,
    fontSize: 15,
    marginBottom: 12,
  },
  searchBtn: {
    backgroundColor: '#1d3557',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 4,
  },
  searchBtnText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: 'bold',
  },
  resultCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 20,
    shadowColor: '#000',
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingBottom: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
    marginBottom: 10,
  },
  resCodeText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#212529',
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  statusBadgeText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  infoLabel: {
    fontSize: 14,
    color: '#6c757d',
  },
  infoValue: {
    fontSize: 14,
    color: '#212529',
    fontWeight: '500',
  },
  cancelBtn: {
    marginTop: 20,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e63946',
    alignItems: 'center',
  },
  cancelBtnText: {
    color: '#e63946',
    fontSize: 14,
    fontWeight: 'bold',
  },
  disabledBtn: {
    opacity: 0.5,
  },
});
