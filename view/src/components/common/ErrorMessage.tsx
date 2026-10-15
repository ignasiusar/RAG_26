export default function ErrorMessage({ message }: { message: string }) {
  return <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{message}</p>;
}
