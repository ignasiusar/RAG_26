export default function Header() {
  return (
    <header className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-800 font-semibold text-white">t</div>
        <span className="text-xl font-medium">temukerja</span>
      </div>
      <nav className="flex gap-8 text-sm text-slate-500">
        <a className="text-slate-900" href="#">Jelajahi</a>
        <a href="#">Tersimpan</a>
        <a href="#">Profil</a>
      </nav>
      <span className="text-sm text-slate-500">Konsep UI</span>
    </header>
  );
}
