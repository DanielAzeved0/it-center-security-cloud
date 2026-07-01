import { MachineDetailView } from "@/components/MachineDetailView";

export default async function MachineDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  return <MachineDetailView machineId={id} />;
}
