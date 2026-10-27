// API Client for Restaurant Reservation & Ordering System
// Automatically targets Flask backend at localhost:5000

export const API_BASE_URL = "http://127.0.0.1:5000/api/v1";

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || data.error || "網路請求失敗");
    }
    return data;
  } catch (error) {
    console.error(`API Error on [${options.method || 'GET'}] ${endpoint}:`, error.message);
    throw error;
  }
}

export const MenuAPI = {
  getCategories: () => request("/menu/categories"),
  getItems: (categoryId = null) => {
    const query = categoryId ? `?category_id=${categoryId}` : "";
    return request(`/menu${query}`);
  },
  getItemDetail: (itemId) => request(`/menu/${itemId}`)
};

export const ReservationAPI = {
  createReservation: (reservationData) => {
    return request("/reservations", {
      method: "POST",
      body: JSON.stringify(reservationData)
    });
  },
  getReservation: (code, phone) => {
    return request(`/reservations/${encodeURIComponent(code)}?phone=${encodeURIComponent(phone)}`);
  },
  cancelReservation: (code, phone) => {
    return request(`/reservations/${encodeURIComponent(code)}/cancel`, {
      method: "POST",
      body: JSON.stringify({ phone })
    });
  }
};

export const OrderAPI = {
  createDineInOrder: (tableId, items) => {
    return request("/orders", {
      method: "POST",
      body: JSON.stringify({ table_id: tableId, items })
    });
  },
  getOrder: (orderId) => request(`/orders/${orderId}`)
};
