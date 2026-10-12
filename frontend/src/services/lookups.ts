import { useSuspenseQuery, type QueryClient } from "@tanstack/react-query";
import { q } from "./api";

export const ensureLookups = (qc: QueryClient) =>
  Promise.all([qc.ensureQueryData(q.customers()), qc.ensureQueryData(q.vehicles()), qc.ensureQueryData(q.technicians()), qc.ensureQueryData(q.bays())]);

export function useLookups() {
  const { data: customers } = useSuspenseQuery(q.customers());
  const { data: vehicles } = useSuspenseQuery(q.vehicles());
  const { data: technicians } = useSuspenseQuery(q.technicians());
  const { data: bays } = useSuspenseQuery(q.bays());
  return {
    customers, vehicles, technicians, bays,
    customer: (id: string) => customers.find((c) => c.id === id),
    vehicle: (id: string) => vehicles.find((v) => v.id === id),
    tech: (id: string | null) => technicians.find((t) => t.id === id),
    bay: (id: string | null) => bays.find((b) => b.id === id),
  };
}
