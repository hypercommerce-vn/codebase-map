export type Service = {
  id: string;
  name: string;
  priceVnd: number;
  minutes: number;
};

export type Customer = {
  id: string;
  name: string;
  phone: string;
  note?: string;
};

export type BookingStatus = "booked" | "done" | "cancelled";

export type Booking = {
  id: string;
  customerId: string;
  serviceId: string;
  startsAt: string;
  status: BookingStatus;
};

export type Slot = {
  startsAt: string;
  taken: boolean;
};
