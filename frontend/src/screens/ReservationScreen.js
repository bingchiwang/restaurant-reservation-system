import React, { useState, useMemo, useEffect } from 'react';
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
import { useCart } from '../context/CartContext';
import { useSystemConfig } from '../context/SystemConfigContext';

function buildTimeSlots(openStr, closeStr) {
  const [oh, om] = (openStr || '11:00').split(':').map(Number);
  const [ch, cm] = (closeStr || '21:30').split(':').map(Number);
  const startMin = oh * 60 + om;
  const endMin = ch * 60 + cm;
  const slots = [];
  for (let m = startMin; m <= endMin; m += 30) {
    const hh = String(Math.floor(m / 60)).padStart(2, '0');
    const mm = String(m % 60).padStart(2, '0');
    slots.push(`${hh}:${mm}`);
  }
  return slots;
}

export default function ReservationScreen({ onBookingSuccess }) {
  const { config } = useSystemConfig();
  const availableTimes = useMemo(
    () => buildTimeSlots(config.opening_time, config.closing_time),
    [config.opening_time, config.closing_time]
  );

  const [partySize, setPartySize] = useState(2);
  const [selectedDate, setSelectedDate] = useState(() => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  });
  const [selectedTime, setSelectedTime] = useState("12:00");
  const [guestName, setGuestName] = useState("");
  const [guestPhone, setGuestPhone] = useState("");
  const [note, setNote] = useState("");
  const [includePreOrder, setIncludePreOrder] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [confirmedBooking, setConfirmedBooking] = useState(null);

  const { cartItems, totalAmount, totalCount, clearCart } = useCart();

  useEffect(() => {
    if (availableTimes.length > 0 && !availableTimes.includes(selectedTime)) {
      setSelectedTime(availableTimes[0]);
    }
  }, [availableTimes, selectedTime]);

  const canReserve = config.store_status === 'OPEN' && config.reservations_enabled;
  const canPreOrder = canReserve && config.pre_order_enabled && config.ordering_enabled;

  const handleBooking = async () => {
    if (!canReserve) {
      Alert.alert("暫停預約", "目前本店暫停線上預約服務");
      return;
    }
    if (!guestName.trim()) {
      Alert.alert("請填寫姓名", "請輸入訂位聯絡人姓名");
      return;
    }
    if (!guestPhone.trim() || guestPhone.length < 8) {
      Alert.alert("請填寫有效電話", "請輸入正確的聯絡電話，以利預約查詢核對");
      return;
    }

    const reservationTime = `${selectedDate} ${selectedTime}`;
    const payload = {
      party_size: partySize,
      reservation_time: reservationTime,
      guest_name: guestName.trim(),
      guest_phone: guestPhone.trim(),
      note: note.trim()
    };

    if (canPreOrder && includePreOrder && cartItems.length > 0) {
      payload.items = cartItems.map(i => ({
        item_id: i.item_id,
        quantity: i.quantity,
        note: i.note
      }));
    }

    setSubmitting(true);
    try {
      const res = await ReservationAPI.createReservation(payload);
      if (res.success) {
        setConfirmedBooking(res.data);
        if (canPreOrder && includePreOrder && cartItems.length > 0) {
          clearCart();
        }
      }
    } catch (err) {
      Alert.alert("預約未成功", err.message || "目前該時段無合適桌位或系統繁忙");
    } finally {
      setSubmitting(false);
    }
  };

  const handleReset = () => {
    setConfirmedBooking(null);
    setGuestName("");
    setGuestPhone("");
    setNote("");
  };

  if (confirmedBooking) {
    return (
      <ScrollView contentContainerStyle={styles.successContainer}>
        <View style={styles.successCard}>
          <Text style={styles.successIcon}>🎉</Text>
          <Text style={styles.successTitle}>預約成功！</Text>
          <Text style={styles.successSubtitle}>我們已為您保留專屬桌位</Text>

          <View style={styles.codeBox}>
            <Text style={styles.codeLabel}>您的預約編號</Text>
            <Text style={styles.codeValue}>{confirmedBooking.reservation_code}</Text>
          </View>

          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>預約姓名</Text>
            <Text style={styles.detailValue}>{confirmedBooking.guest_name}</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>聯絡電話</Text>
            <Text style={styles.detailValue}>{confirmedBooking.guest_phone}</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>用餐時段</Text>
            <Text style={styles.detailValue}>{confirmedBooking.start_at}</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>用餐人數</Text>
            <Text style={styles.detailValue}>{confirmedBooking.party_size} 位</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>分配桌號</Text>
            <Text style={[styles.detailValue, styles.highlightValue]}>
              {confirmedBooking.table_name || `桌號 #${confirmedBooking.table_id}`}
            </Text>
          </View>

          {confirmedBooking.pre_order && (
            <View style={styles.preOrderBox}>
              <Text style={styles.preOrderTitle}>已完成預先點餐</Text>
              <Text style={styles.preOrderAmount}>
                共 {confirmedBooking.pre_order.items?.length || 0} 道餐點，總額 NT$ {confirmedBooking.pre_order.total_amount}
              </Text>
            </View>
          )}

          <TouchableOpacity style={styles.primaryButton} onPress={handleReset}>
            <Text style={styles.primaryButtonText}>建立另一筆預約</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {!canReserve && (
        <View style={styles.pausedCard}>
          <Text style={styles.pausedTitle}>⚠️ 目前暫停線上預約服務</Text>
          <Text style={styles.pausedSub}>
            {config.store_status === 'CLOSED'
              ? '本店目前處於非營業時間／休息中。'
              : '餐廳管理員已暫時關閉線上預約功能，如有需要請電洽門市。'}
          </Text>
        </View>
      )}

      <Text style={styles.sectionTitle}>1. 選擇人數</Text>
      <View style={styles.partySizeSelector}>
        {[1, 2, 3, 4, 5, 6, 8].map(size => (
          <TouchableOpacity
            key={size}
            style={[styles.sizeChip, partySize === size && styles.sizeChipActive]}
            onPress={() => setPartySize(size)}
          >
            <Text style={[styles.sizeChipText, partySize === size && styles.sizeChipTextActive]}>
              {size} 人
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.sectionTitle}>
        2. 用餐日期與時段 ({config.opening_time} ~ {config.closing_time})
      </Text>
      <View style={styles.inputGroup}>
        <Text style={styles.inputLabel}>預約日期 (YYYY-MM-DD)</Text>
        <TextInput
          style={styles.input}
          value={selectedDate}
          onChangeText={setSelectedDate}
          placeholder="例如 2026-10-28"
        />
      </View>

      <Text style={styles.inputLabel}>選擇時段</Text>
      <View style={styles.timeGrid}>
        {availableTimes.map(time => (
          <TouchableOpacity
            key={time}
            style={[styles.timeChip, selectedTime === time && styles.timeChipActive]}
            onPress={() => setSelectedTime(time)}
          >
            <Text style={[styles.timeChipText, selectedTime === time && styles.timeChipTextActive]}>
              {time}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.sectionTitle}>3. 訂位聯絡資料 (訪客免註冊)</Text>
      <View style={styles.inputGroup}>
        <Text style={styles.inputLabel}>聯絡人姓名 *</Text>
        <TextInput
          style={styles.input}
          value={guestName}
          onChangeText={setGuestName}
          placeholder="請輸入姓名"
        />
      </View>

      <View style={styles.inputGroup}>
        <Text style={styles.inputLabel}>聯絡電話 (查詢預約核對用) *</Text>
        <TextInput
          style={styles.input}
          value={guestPhone}
          onChangeText={setGuestPhone}
          placeholder="例如 0912345678"
          keyboardType="phone-pad"
        />
      </View>

      <View style={styles.inputGroup}>
        <Text style={styles.inputLabel}>用餐備註 (可選)</Text>
        <TextInput
          style={[styles.input, styles.textArea]}
          value={note}
          onChangeText={setNote}
          placeholder="例如：需兒童座椅、有長輩同行等"
          multiline
          numberOfLines={2}
        />
      </View>

      {/* Pre-order banner if cart has items */}
      {cartItems.length > 0 && (
        <View style={styles.cartLinkBanner}>
          <View style={{ flex: 1 }}>
            <Text style={styles.cartBannerTitle}>購物車已有 {totalCount} 件餐點 (NT$ {totalAmount})</Text>
            <Text style={styles.cartBannerSubtitle}>
              {canPreOrder ? "可於預約時直接提前送單備餐" : "目前餐廳暫停預約預點餐，本單將僅建立訂位"}
            </Text>
          </View>
          {canPreOrder && (
            <TouchableOpacity
              style={[styles.checkbox, includePreOrder && styles.checkboxActive]}
              onPress={() => setIncludePreOrder(!includePreOrder)}
            >
              <Text style={styles.checkboxText}>{includePreOrder ? '✓ 預點餐' : '不預點'}</Text>
            </TouchableOpacity>
          )}
        </View>
      )}

      <TouchableOpacity
        style={[styles.submitButton, (submitting || !canReserve) && styles.submitButtonDisabled]}
        onPress={handleBooking}
        disabled={submitting || !canReserve}
      >
        {submitting ? (
          <ActivityIndicator color="#ffffff" />
        ) : (
          <Text style={styles.submitButtonText}>
            {canReserve ? "確認並提交預約" : "目前暫停線上預約"}
          </Text>
        )}
      </TouchableOpacity>
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
    paddingBottom: 40,
  },
  pausedCard: {
    backgroundColor: '#fff3cd',
    borderWidth: 1,
    borderColor: '#ffe69c',
    borderRadius: 10,
    padding: 14,
    marginBottom: 14,
  },
  pausedTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#664d03',
    marginBottom: 4,
  },
  pausedSub: {
    fontSize: 12,
    color: '#664d03',
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1d3557',
    marginTop: 14,
    marginBottom: 10,
  },
  partySizeSelector: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 10,
  },
  sizeChip: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#dee2e6',
  },
  sizeChipActive: {
    backgroundColor: '#e63946',
    borderColor: '#e63946',
  },
  sizeChipText: {
    fontSize: 14,
    color: '#495057',
    fontWeight: '600',
  },
  sizeChipTextActive: {
    color: '#ffffff',
  },
  inputGroup: {
    marginBottom: 14,
  },
  inputLabel: {
    fontSize: 13,
    color: '#6c757d',
    marginBottom: 6,
    fontWeight: '500',
  },
  input: {
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#ced4da',
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10,
    fontSize: 15,
    color: '#212529',
  },
  textArea: {
    height: 60,
    textAlignVertical: 'top',
  },
  timeGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 14,
  },
  timeChip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 6,
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#dee2e6',
  },
  timeChipActive: {
    backgroundColor: '#1d3557',
    borderColor: '#1d3557',
  },
  timeChipText: {
    fontSize: 13,
    color: '#495057',
  },
  timeChipTextActive: {
    color: '#ffffff',
    fontWeight: 'bold',
  },
  cartLinkBanner: {
    backgroundColor: '#e8f4f8',
    borderRadius: 10,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 14,
    borderWidth: 1,
    borderColor: '#bce0fd',
  },
  cartBannerTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1d3557',
  },
  cartBannerSubtitle: {
    fontSize: 12,
    color: '#457b9d',
    marginTop: 2,
  },
  checkbox: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    backgroundColor: '#ced4da',
  },
  checkboxActive: {
    backgroundColor: '#2a9d8f',
  },
  checkboxText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  submitButton: {
    backgroundColor: '#e63946',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 16,
    shadowColor: '#e63946',
    shadowOpacity: 0.3,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 3 },
    elevation: 4,
  },
  submitButtonDisabled: {
    backgroundColor: '#adb5bd',
  },
  submitButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  successContainer: {
    flexGrow: 1,
    padding: 20,
    justifyContent: 'center',
  },
  successCard: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 5,
  },
  successIcon: {
    fontSize: 48,
    marginBottom: 10,
  },
  successTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#1d3557',
  },
  successSubtitle: {
    fontSize: 14,
    color: '#6c757d',
    marginTop: 4,
    marginBottom: 20,
  },
  codeBox: {
    backgroundColor: '#f1faee',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    alignItems: 'center',
    width: '100%',
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#a8dadc',
  },
  codeLabel: {
    fontSize: 12,
    color: '#457b9d',
  },
  codeValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#e63946',
    letterSpacing: 1,
    marginTop: 4,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f3f5',
  },
  detailLabel: {
    fontSize: 14,
    color: '#6c757d',
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#212529',
  },
  highlightValue: {
    color: '#1d3557',
    fontWeight: 'bold',
  },
  preOrderBox: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 12,
    width: '100%',
    marginTop: 14,
    borderLeftWidth: 4,
    borderLeftColor: '#2a9d8f',
  },
  preOrderTitle: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#2a9d8f',
  },
  preOrderAmount: {
    fontSize: 12,
    color: '#495057',
    marginTop: 2,
  },
  primaryButton: {
    backgroundColor: '#1d3557',
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 24,
    marginTop: 24,
    width: '100%',
    alignItems: 'center',
  },
  primaryButtonText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '600',
  },
});
