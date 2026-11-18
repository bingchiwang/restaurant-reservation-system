// API Client for Restaurant Reservation & Ordering System
// Uses same-origin /api/v1 when hosted by Flask (:5000), falling back to 127.0.0.1:5000 for local Metro dev

const getApiBaseUrl = () => {
  if (typeof window !== "undefined" && window.location) {
    const { protocol, port, origin } = window.location;
    if (protocol.startsWith("http") && port !== "8081") {
      return `${origin}/api/v1`;
    }
  }
  return "http://127.0.0.1:5000/api/v1";
};

export const API_BASE_URL = getApiBaseUrl();

async function request(endpoint, options = {}, token = null) {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

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

export const SystemAPI = {
  getConfig: () => request("/system/config")
};

export const MemberAPI = {
  login: (email, password) =>
    request("/auth/member/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    }),
  register: (email, password, displayName, phone, gender, birthday) =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify({
        email,
        password,
        display_name: displayName,
        phone,
        gender,
        birthday
      })
    }),
  logout: () =>
    request("/auth/logout", {
      method: "POST"
    }),
  getProfile: (token) => request("/me", {}, token),
  updateProfile: (token, data) =>
    request(
      "/me",
      {
        method: "PATCH",
        body: JSON.stringify(data)
      },
      token
    ),
  getMyReservations: (token) => request("/me/reservations", {}, token),
  getMyOrders: (token) => request("/me/orders", {}, token)
};

export const MenuAPI = {
  getCategories: () => request("/menu/categories"),
  getItems: (categoryId = null) => {
    const query = categoryId ? `?category_id=${categoryId}` : "";
    return request(`/menu${query}`);
  },
  getItemDetail: (itemId) => request(`/menu/${itemId}`)
};

export const ReservationAPI = {
  createReservation: (reservationData, token = null) => {
    return request(
      "/reservations",
      {
        method: "POST",
        body: JSON.stringify(reservationData)
      },
      token
    );
  },
  getReservation: (code, phone, token = null) => {
    const query = phone ? `?phone=${encodeURIComponent(phone)}` : "";
    return request(`/reservations/${encodeURIComponent(code)}${query}`, {}, token);
  },
  cancelReservation: (code, phone = null, token = null) => {
    return request(
      `/reservations/${encodeURIComponent(code)}/cancel`,
      {
        method: "POST",
        body: JSON.stringify(phone ? { phone } : {})
      },
      token
    );
  }
};

export const OrderAPI = {
  createDineInOrder: (tableId, items, token = null) => {
    return request(
      "/orders",
      {
        method: "POST",
        body: JSON.stringify({ table_id: tableId, items })
      },
      token
    );
  },
  getOrder: (orderId, token = null) => request(`/orders/${orderId}`, {}, token)
};
