import {
    memo,
    useCallback,
    useEffect,
    useRef,
    useState,
    type FormEvent,
} from "react";

import {
    ArrowRight,
    ArrowUp,
    ArrowUpRight,
    BriefcaseBusiness,
    Clock3,
    Compass,
    ExternalLink,
    Eye,
    EyeOff,
    FileText,
    LoaderCircle,
    LogOut,
    Menu,
    MessageSquare,
    Moon,
    Pencil,
    Plus,
    Search,
    Sparkles,
    Sun,
    Trash2,
    X,
    Zap,
} from "lucide-react";

import ReactMarkdown from "react-markdown";

import {
    api,
    ApiError,
    hasToken,
    setToken,
    type Conversation,
    type Message,
    type Quota,
    type User,
} from "./services/ragApi";

const suggestions = [
    {
        icon: BriefcaseBusiness,
        title: "Temukan lowongan",
        text: "Cari lowongan drafter di Jakarta",
    },
    {
        icon: Compass,
        title: "Rencanakan karier",
        text: "Aku lulusan teknik sipil. Bagaimana memulai karierku?",
    },
    {
        icon: FileText,
        title: "Rapikan CV",
        text: "Bagaimana membuat CV yang ATS friendly?",
    },
    {
        icon: MessageSquare,
        title: "Siapkan interview",
        text: "Bantu aku berlatih interview untuk posisi engineer",
    },
];

const errorText = (error: unknown) =>
    error instanceof Error
        ? error.message
        : "Ada kendala. Silakan coba lagi.";

const timeLabel = (timestamp: number) =>
    new Date(timestamp * 1000).toLocaleTimeString(
        "id-ID",
        {
            hour: "2-digit",
            minute: "2-digit",
        },
    );

const countdown = (seconds: number) =>
    `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(
        seconds % 60,
    ).padStart(2, "0")}`;

function safeLink(value: string) {
    try {
        const url = new URL(value);

        return ["http:", "https:"].includes(url.protocol)
            ? url.href
            : undefined;
    } catch {
        return undefined;
    }
}

function initialTheme(): "light" | "dark" {
    try {
        const value = localStorage.getItem(
            "temukerja.theme",
        );

        if (value === "dark" || value === "light") {
            return value;
        }
    } catch {
        // Tema tetap bekerja tanpa penyimpanan browser.
    }

    return window.matchMedia(
        "(prefers-color-scheme: dark)",
    ).matches
        ? "dark"
        : "light";
}

function Brand() {
    return (
        <div className="brand">
            <span className="brand-mark">
                <BriefcaseBusiness size={22} />
            </span>

            <span>
                TemuKerja
                <span className="brand-ai">AI</span>
            </span>
        </div>
    );
}

function BackgroundDecor() {
  return (
    <div
      className="tk-world tk-round-decor"
      aria-hidden="true"
    >
      {Array.from({ length: 9 }, (_, i) => (
        <span
          key={i}
          className={`tk-circle tk-circle-${i + 1}`}
        />
      ))}

      <span className="tk-plus tk-plus-1">+</span>
      <span className="tk-plus tk-plus-2">+</span>
      <span className="tk-plus tk-plus-3">+</span>
    </div>
  );
}

function Auth({
  onSuccess,
  theme,
  toggleTheme,
  notice,
}: {
  onSuccess: (u: User) => void;
  theme: string;
  toggleTheme: () => void;
  notice: string;
}) {
  const [register, setRegister] = useState(false);
  const [show, setShow] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (busy) return;

    setBusy(true);
    setError("");

    try {
      if (register) {
        await api.register(
          name.trim(),
          email.trim(),
          password
        );

        setRegister(false);
        setInfo("Akun berhasil dibuat. Silakan masuk.");
      }

      onSuccess(
        await api.login(email.trim(), password)
      );
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page tk-auth">
      <BackgroundDecor />

      <section className="tk-auth-art">
        <Brand />
       <h1 className="tk-welcome-left">
            <span>Selamat</span>
            <span>datang.</span>
        </h1>
      </section>

      <section className="auth-form-section">
        <button
          className="icon-button auth-theme"
          type="button"
          aria-label={
            theme === "light"
              ? "Aktifkan tema gelap"
              : "Aktifkan tema terang"
          }
          onClick={toggleTheme}
        >
          {theme === "light"
            ? <Moon size={20} />
            : <Sun size={20} />}
        </button>

        <div className="auth-form-wrap">
          <div className="auth-mobile-brand">
            <Brand />
          </div>

          <h2>{register ? "DAFTAR" : "MASUK"}</h2>

          <p className="muted">
            {register
              ? "Mulai perjalanan kariermu."
              : "Lanjutkan langkah kariermu."}
          </p>

          {notice && (
            <p className="notice" role="status">
              {notice}
            </p>
          )}

          {info && (
            <p className="notice" role="status">
              {info}
            </p>
          )}

          {error && (
            <p className="error-box" role="alert">
              {error}
            </p>
          )}

          <form
            onSubmit={submit}
            className="auth-form"
          >
            {register && (
              <label>
                Nama lengkap
                <input
                  autoComplete="name"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  minLength={2}
                  maxLength={80}
                  required
                  placeholder="Nama kamu"
                  disabled={busy}
                />
              </label>
            )}

            <label>
              Email
              <input
                type="email"
                autoComplete="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                maxLength={254}
                required
                placeholder="nama@email.com"
                disabled={busy}
              />
            </label>

            <label>
              Password
              <div className="password-field">
                <input
                  type={show ? "text" : "password"}
                  autoComplete={
                    register
                      ? "new-password"
                      : "current-password"
                  }
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  minLength={8}
                  maxLength={128}
                  required
                  placeholder={
                    register
                      ? "Minimal 8 karakter"
                      : "Password kamu"
                  }
                  disabled={busy}
                />

                <button
                  type="button"
                  className="icon-button"
                  aria-label={
                    show
                      ? "Sembunyikan password"
                      : "Tampilkan password"
                  }
                  onClick={() => setShow(!show)}
                >
                  {show
                    ? <EyeOff size={18} />
                    : <Eye size={18} />}
                </button>
              </div>
            </label>

            <button
              className="primary auth-submit"
              disabled={busy}
            >
              {busy ? (
                <LoaderCircle
                  className="spin"
                  size={19}
                />
              ) : (
                <>
                  {register ? "Buat akun" : "Masuk"}
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>

          <p className="tk-auth-switch">
            {register
              ? "Sudah punya akun?"
              : "Belum punya akun?"}

            <button
              type="button"
              disabled={busy}
              onClick={() => {
                setRegister(!register);
                setError("");
                setInfo("");
              }}
            >
              {register ? "Masuk" : "Daftar"}
            </button>
          </p>
        </div>
      </section>
    </main>
  );
}

const MessageCard = memo(function MessageCard({
    message,
}: {
    message: Message;
}) {
    const user = message.role === "user";

    return (
        <article
            className={`message ${
                user
                    ? "message-user"
                    : "message-assistant"
            }`}
        >
            {!user && (
                <div className="message-logo">
                    <Sparkles size={18} />
                </div>
            )}

            <div className="message-body">
                <span className="message-name">
                    {user ? "Kamu" : "TemuKerja"}
                    <time>
                        {timeLabel(message.created_at)}
                    </time>
                </span>

                <div className="message-text">
                    {user ? (
                        <p>{message.content}</p>
                    ) : (
                        <ReactMarkdown
                            components={{
                                a: ({ href, children }) => (
                                    <a
                                        href={href}
                                        target="_blank"
                                        rel="noreferrer"
                                    >
                                        {children}
                                    </a>
                                ),
                            }}
                        >
                            {message.content}
                        </ReactMarkdown>
                    )}
                </div>

                {!user && message.sources.length > 0 && (
                    <div className="sources">
                        <span className="source-label">
                            SUMBER LOWONGAN
                        </span>

                        {message.sources.map((source, index) => {
                            const href = safeLink(source.url);

                            return (
                                href && (
                                    <a
                                        key={`${source.url}-${index}`}
                                        href={href}
                                        target="_blank"
                                        rel="noreferrer"
                                        className="source-card"
                                    >
                                        <BriefcaseBusiness size={17} />

                                        <span>
                                            <strong>
                                                {source.posisi}
                                            </strong>
                                            <small>
                                                {source.perusahaan}
                                                {" · "}
                                                {source.lokasi}
                                            </small>
                                        </span>

                                        <ExternalLink size={15} />
                                    </a>
                                )
                            );
                        })}
                    </div>
                )}
            </div>
        </article>
    );
});

export default function App() {
    const [theme, setTheme] = useState(initialTheme);
    const [user, setUser] = useState<User | null>(null);
    const [booting, setBooting] = useState(true);
    const [notice, setNotice] = useState("");

    const [list, setList] = useState<Conversation[]>([]);
    const [more, setMore] = useState(false);
    const [search, setSearch] = useState("");
    const [listLoading, setListLoading] = useState(false);
    const [revision, setRevision] = useState(0);

    const [selected, setSelected] =
        useState<Conversation | null>(null);

    const [items, setItems] = useState<Message[]>([]);
    const [text, setText] = useState("");
    const [quota, setQuota] = useState<Quota | null>(null);
    const [offset, setOffset] = useState(0);
    const [now, setNow] = useState(Date.now());

    const [busy, setBusy] = useState<
        "send" | "load" | "edit" | "logout" | null
    >(null);

    const [error, setError] = useState("");
    const [menu, setMenu] = useState(false);

    const [dialogMode, setDialogMode] = useState<
        "rename" | "delete" | null
    >(null);

    const [title, setTitle] = useState("");
    const [dialogError, setDialogError] = useState("");

    const dialog = useRef<HTMLDialogElement>(null);
    const bottom = useRef<HTMLDivElement>(null);
    const input = useRef<HTMLTextAreaElement>(null);

    const epoch = useRef(0);
    const searchRevision = useRef(0);
    const quotaRevision = useRef(0);

    const toggleTheme = () =>
        setTheme(current =>
            current === "light" ? "dark" : "light",
        );

    const updateQuota = useCallback((value: Quota) => {
        const serverTime =
            value.server_time ?? Date.now() / 1000;

        if (serverTime < quotaRevision.current) return;

        quotaRevision.current = serverTime;
        setQuota(value);
        setOffset(serverTime - Date.now() / 1000);
    }, []);

    const clearSession = useCallback(
        (keepToken = false) => {
            epoch.current++;
            quotaRevision.current = 0;

            if (!keepToken) setToken(null);

            setUser(null);
            setList([]);
            setSelected(null);
            setItems([]);
            setQuota(null);
            setText("");
            setBusy(null);
            setSearch("");
            setError("");
            setMenu(false);
        },
        [],
    );

    useEffect(() => {
        document.documentElement.dataset.theme = theme;
        document.documentElement.style.colorScheme = theme;

        try {
            localStorage.setItem(
                "temukerja.theme",
                theme,
            );
        } catch {
            // Pilihan tema tetap berlaku pada halaman ini.
        }
    }, [theme]);

    useEffect(() => {
        let active = true;

        const expired = () => {
            clearSession();
            setNotice(
                "Sesi berakhir. Masuk kembali untuk melanjutkan.",
            );
        };

        window.addEventListener(
            "temukerja:expired",
            expired,
        );

        if (hasToken()) {
            api.me()
                .then(value => {
                    if (active) setUser(value);
                })
                .catch(err => {
                    if (active) setNotice(errorText(err));
                })
                .finally(() => {
                    if (active) setBooting(false);
                });
        } else {
            setBooting(false);
        }

        return () => {
            active = false;

            window.removeEventListener(
                "temukerja:expired",
                expired,
            );
        };
    }, [clearSession]);

    useEffect(() => {
        if (!user) return;

        const stamp = epoch.current;
        let active = true;

        async function refresh() {
            try {
                const value = await api.quota();

                if (
                    active &&
                    stamp === epoch.current
                ) {
                    updateQuota(value);
                }
            } catch (err) {
                if (
                    active &&
                    stamp === epoch.current
                ) {
                    setError(errorText(err));
                }
            }
        }

        void refresh();

        const timer = setInterval(refresh, 15000);

        const tick = setInterval(
            () => setNow(Date.now()),
            1000,
        );

        window.addEventListener("focus", refresh);

        return () => {
            active = false;
            clearInterval(timer);
            clearInterval(tick);
            window.removeEventListener("focus", refresh);
        };
    }, [user, updateQuota]);

    const seconds =
        quota?.blocked && quota.reset_at
            ? Math.max(
                  0,
                  Math.ceil(
                      quota.reset_at -
                          (now / 1000 + offset),
                  ),
              )
            : 0;

    useEffect(() => {
        if (
            !user ||
            !quota?.blocked ||
            seconds !== 0
        ) {
            return;
        }

        const stamp = epoch.current;

        api.quota()
            .then(value => {
                if (stamp === epoch.current) {
                    updateQuota(value);
                }
            })
            .catch(() => {
                // Penyegaran berkala akan mencoba kembali.
            });
    }, [
        user,
        quota?.blocked,
        quota?.reset_at,
        seconds,
        updateQuota,
    ]);

    useEffect(() => {
        if (!user) return;

        let active = true;
        const stamp = epoch.current;

        searchRevision.current++;
        setListLoading(true);

        const timer = setTimeout(() => {
            api.conversations(0, search)
                .then(data => {
                    if (
                        active &&
                        stamp === epoch.current
                    ) {
                        setList(data.items);
                        setMore(data.has_more);
                    }
                })
                .catch(err => {
                    if (
                        active &&
                        stamp === epoch.current
                    ) {
                        setError(errorText(err));
                    }
                })
                .finally(() => {
                    if (
                        active &&
                        stamp === epoch.current
                    ) {
                        setListLoading(false);
                    }
                });
        }, 200);

        return () => {
            active = false;
            clearTimeout(timer);
        };
    }, [user, search, revision]);

    useEffect(() => {
        bottom.current?.scrollIntoView({
            behavior: window.matchMedia(
                "(prefers-reduced-motion: reduce)",
            ).matches
                ? "auto"
                : "smooth",
            block: "end",
        });
    }, [items, busy]);

    useEffect(() => {
        if (!input.current) return;

        input.current.style.height = "auto";

        input.current.style.height = `${Math.min(
            input.current.scrollHeight,
            160,
        )}px`;
    }, [text, user]);

    useEffect(() => {
        const close = (event: globalThis.KeyboardEvent) => {
            if (event.key === "Escape") {
                setMenu(false);
            }
        };

        window.addEventListener("keydown", close);

        return () =>
            window.removeEventListener("keydown", close);
    }, []);

    function newChat() {
        if (busy) return;

        setSelected(null);
        setItems([]);
        setText("");
        setError("");
        setMenu(false);

        input.current?.focus();
    }

    async function openConversation(
        conversation: Conversation,
    ) {
        if (busy) return;

        const stamp = epoch.current;

        setBusy("load");
        setError("");
        setMenu(false);

        try {
            const data = await api.conversation(
                conversation.id,
            );

            if (stamp === epoch.current) {
                setSelected(data.conversation);
                setItems(data.messages);
                setText("");
            }
        } catch (err) {
            if (stamp === epoch.current) {
                setError(errorText(err));
            }
        } finally {
            if (stamp === epoch.current) {
                setBusy(null);
            }
        }
    }

    async function loadMore() {
        const stamp = epoch.current;
        const version = searchRevision.current;

        setListLoading(true);

        try {
            const data = await api.conversations(
                list.length,
                search,
            );

            if (
                stamp === epoch.current &&
                version === searchRevision.current
            ) {
                setList(current => [
                    ...current,
                    ...data.items,
                ]);

                setMore(data.has_more);
            }
        } catch (err) {
            if (stamp === epoch.current) {
                setError(errorText(err));
            }
        } finally {
            if (
                stamp === epoch.current &&
                version === searchRevision.current
            ) {
                setListLoading(false);
            }
        }
    }

    async function send(content = text) {
        const clean = content.trim();

        if (
            !clean ||
            busy ||
            !quota ||
            quota.blocked
        ) {
            return;
        }

        const stamp = epoch.current;
        const optimisticId = `pending-${Date.now()}`;

        setBusy("send");
        setError("");
        setText("");

        setItems(current => [
            ...current,
            {
                id: optimisticId,
                role: "user",
                content: clean,
                sources: [],
                created_at: Date.now() / 1000,
            },
        ]);

        try {
            let conversation = selected;

            if (!conversation) {
                conversation = await api.create(
                    clean.slice(0, 80),
                );

                if (stamp !== epoch.current) return;

                setSelected(conversation);
                setRevision(value => value + 1);
            }

            const data = await api.chat(
                conversation.id,
                clean,
            );

            if (stamp !== epoch.current) return;

            setItems(current => [
                ...current.filter(
                    item => item.id !== optimisticId,
                ),
                ...data.messages,
            ]);

            updateQuota(data.quota);
            setRevision(value => value + 1);
        } catch (err) {
            if (stamp !== epoch.current) return;

            setItems(current =>
                current.filter(
                    item => item.id !== optimisticId,
                ),
            );

            setText(clean);
            setError(errorText(err));

            if (err instanceof ApiError && err.quota) {
                updateQuota(err.quota);
            }
        } finally {
            if (stamp === epoch.current) {
                setBusy(null);

                setTimeout(
                    () => input.current?.focus(),
                    0,
                );
            }
        }
    }

    function openDialog(
        mode: "rename" | "delete",
    ) {
        if (!selected || busy) return;

        setTitle(selected.title);
        setDialogError("");
        setDialogMode(mode);

        dialog.current?.showModal();
    }

    async function submitDialog(
        event: FormEvent,
    ) {
        event.preventDefault();

        if (!selected || busy) return;

        const stamp = epoch.current;

        setBusy("edit");
        setDialogError("");

        try {
            if (dialogMode === "rename") {
                const conversation = await api.rename(
                    selected.id,
                    title.trim(),
                );

                if (stamp === epoch.current) {
                    setSelected(conversation);
                }
            } else {
                await api.remove(selected.id);

                if (stamp === epoch.current) {
                    setSelected(null);
                    setItems([]);
                    setText("");
                }
            }

            if (stamp === epoch.current) {
                setRevision(value => value + 1);
                dialog.current?.close();
            }
        } catch (err) {
            if (stamp === epoch.current) {
                setDialogError(errorText(err));
            }
        } finally {
            if (stamp === epoch.current) {
                setBusy(null);
            }
        }
    }

    async function logout() {
        if (busy) return;

        const stamp = epoch.current;
        setBusy("logout");

        try {
            await api.logout();
        } catch {
            // Tetap keluar dari perangkat ini jika server offline.
        } finally {
            if (stamp === epoch.current) {
                clearSession();

                setNotice(
                    "Kamu sudah keluar dari perangkat ini.",
                );
            }
        }
    }

    if (booting) {
        return (
            <main className="boot-screen">
                <Brand />
                <LoaderCircle
                    size={25}
                    className="spin"
                />
                <p>Menyiapkan ruang kerjamu…</p>
            </main>
        );
    }

    if (!user) {
        return (
            <Auth
                onSuccess={value => {
                    clearSession(true);
                    setUser(value);
                    setNotice("");
                }}
                theme={theme}
                toggleTheme={toggleTheme}
                notice={notice}
            />
        );
    }

    const disabled =
        Boolean(busy) ||
        !quota ||
        quota.blocked;

    return (
        <div className="workspace">
            {menu && (
                <button
                    className="sidebar-backdrop"
                    aria-label="Tutup sidebar"
                    onClick={() => setMenu(false)}
                />
            )}

            <aside
                className={`sidebar ${
                    menu ? "sidebar-open" : ""
                }`}
            >
                <div className="sidebar-brand">
                    <Brand />

                    <button
                        className="icon-button mobile-only"
                        aria-label="Tutup sidebar"
                        onClick={() => setMenu(false)}
                    >
                        <X size={20} />
                    </button>
                </div>

                <button
                    className="primary new-chat"
                    onClick={newChat}
                    disabled={Boolean(busy)}
                >
                    <Plus size={19} />
                    Percakapan baru
                    <span>↗</span>
                </button>

                <label className="history-search">
                    <Search size={17} />

                    <input
                        aria-label="Cari riwayat percakapan"
                        placeholder="Cari percakapan…"
                        value={search}
                        onChange={event =>
                            setSearch(event.target.value)
                        }
                        maxLength={100}
                    />
                </label>

                <div className="history-heading">
                    <span>RIWAYAT PERCAKAPAN</span>

                    {listLoading && (
                        <LoaderCircle
                            size={13}
                            className="spin"
                        />
                    )}
                </div>

                <nav
                    className="history-list"
                    aria-label="Riwayat percakapan"
                >
                    {!listLoading &&
                        list.length === 0 && (
                            <p className="history-empty">
                                {search
                                    ? "Percakapan belum ditemukan."
                                    : "Percakapan pertamamu akan tersimpan di sini."}
                            </p>
                        )}

                    {list.map(conversation => (
                        <button
                            key={conversation.id}
                            className={`history-item ${
                                selected?.id === conversation.id
                                    ? "active"
                                    : ""
                            }`}
                            onClick={() =>
                                openConversation(conversation)
                            }
                            disabled={Boolean(busy)}
                            aria-current={
                                selected?.id === conversation.id
                                    ? "page"
                                    : undefined
                            }
                            title={conversation.title}
                        >
                            <MessageSquare size={16} />
                            <span>{conversation.title}</span>
                        </button>
                    ))}

                    {more && (
                        <button
                            className="load-more"
                            disabled={listLoading}
                            onClick={loadMore}
                        >
                            Muat riwayat lainnya
                        </button>
                    )}
                </nav>

                <section
                    className={`quota-card ${
                        quota?.blocked
                            ? "quota-blocked"
                            : ""
                    }`}
                    aria-label="Kuota AI"
                >
                    <div className="quota-title">
                        <span>
                            <Zap size={15} />
                            Kuota AI
                        </span>

                        <strong>
                            {quota
                                ? `${quota.remaining_percent}%`
                                : "…"}
                        </strong>
                    </div>

                    <div
                        className="quota-meter"
                        role="progressbar"
                        aria-label="Sisa kuota AI"
                        aria-valuemin={0}
                        aria-valuemax={100}
                        aria-valuenow={
                            quota?.remaining_percent ?? 0
                        }
                    >
                        <i
                            style={{
                                width: `${
                                    quota?.remaining_percent ?? 0
                                }%`,
                            }}
                        />
                    </div>

                    <p>
                        {quota?.blocked ? (
                            <>
                                <Clock3 size={13} />
                                Isi ulang dalam{" "}
                                {countdown(seconds)}
                            </>
                        ) : (
                            `${
                                quota?.remaining ?? "…"
                            } dari 100 pesan tersisa`
                        )}
                    </p>

                    <small>
                        Isi ulang 10 menit setelah kuota habis.
                    </small>
                </section>

                <div className="profile">
                    <span className="profile-avatar">
                        {user.name.charAt(0).toUpperCase()}
                    </span>

                    <div>
                        <strong>{user.name}</strong>
                        <small>{user.email}</small>
                    </div>

                    <button
                        className="icon-button"
                        aria-label="Keluar akun"
                        title="Keluar akun"
                        disabled={Boolean(busy)}
                        onClick={logout}
                    >
                        <LogOut size={18} />
                    </button>
                </div>
            </aside>

            <main className="main-panel">
                 <BackgroundDecor />
                <header className="workspace-header">
                    <button
                        className="icon-button mobile-only"
                        aria-label="Buka sidebar"
                        aria-expanded={menu}
                        onClick={() => setMenu(true)}
                    >
                        <Menu size={22} />
                    </button>

                    <div className="header-title">
                        <span>
                            TEMUKERJA / RUANG KERJA
                        </span>

                        <h1>
                            {selected?.title ??
                                "Asisten karier"}
                        </h1>
                    </div>

                    <div className="header-actions">
                        {selected && (
                            <>
                                <button
                                    className="icon-button"
                                    aria-label="Ubah judul percakapan"
                                    title="Ubah judul"
                                    onClick={() =>
                                        openDialog("rename")
                                    }
                                    disabled={Boolean(busy)}
                                >
                                    <Pencil size={17} />
                                </button>

                                <button
                                    className="icon-button"
                                    aria-label="Hapus percakapan"
                                    title="Hapus percakapan"
                                    onClick={() =>
                                        openDialog("delete")
                                    }
                                    disabled={Boolean(busy)}
                                >
                                    <Trash2 size={17} />
                                </button>
                            </>
                        )}

                        <button
                            className="icon-button theme-toggle"
                            aria-label={
                                theme === "light"
                                    ? "Aktifkan tema gelap"
                                    : "Aktifkan tema terang"
                            }
                            onClick={toggleTheme}
                        >
                            {theme === "light" ? (
                                <Moon size={19} />
                            ) : (
                                <Sun size={19} />
                            )}
                        </button>
                    </div>
                </header>

                <div
                    className="chat-scroll"
                    aria-busy={busy === "load"}
                >
                    {busy === "load" ? (
                        <div className="loading-chat">
                            <LoaderCircle className="spin" />
                            Membuka percakapan…
                        </div>
                    ) : items.length === 0 ? (
                        <section className="welcome">
                            <span className="welcome-symbol">
                                <Sparkles size={29} />
                            </span>

                            <p className="welcome-greeting">
                                Halo, {user.name.split(" ")[0]}{" "}
                                <span>✦</span>
                            </p>

                            <h2>
                                Langkah kariermu,
                                <br />
                                <em>mulai lebih terarah.</em>
                            </h2>

                            <p className="welcome-description">
                                Dari mencari peluang sampai
                                mempersiapkan diri.
                                <br />
                                Apa yang ingin kamu diskusikan
                                hari ini?
                            </p>

                            <div className="suggestion-grid">
                                {suggestions.map(suggestion => (
                                    <button
                                        key={suggestion.title}
                                        onClick={() =>
                                            send(suggestion.text)
                                        }
                                        disabled={disabled}
                                    >
                                        <suggestion.icon size={20} />

                                        <strong>
                                            {suggestion.title}
                                        </strong>

                                        <span>
                                            {suggestion.text}
                                        </span>

                                        <ArrowUpRight
                                            className="suggestion-arrow"
                                            size={17}
                                        />
                                    </button>
                                ))}
                            </div>

                            <p className="welcome-note">
                                <BriefcaseBusiness size={14} />
                                Rekomendasi lowongan berdasarkan
                                data yang tersedia.
                            </p>
                        </section>
                    ) : (
                        <section
                            className="messages"
                            aria-label="Isi percakapan"
                        >
                            {items.map(message => (
                                <MessageCard
                                    key={message.id}
                                    message={message}
                                />
                            ))}

                            {busy === "send" && (
                                <div
                                    className="thinking"
                                    role="status"
                                >
                                    <span className="message-logo">
                                        <Sparkles size={18} />
                                    </span>

                                    <span>
                                        <i />
                                        <i />
                                        <i />
                                    </span>

                                    <small>
                                        Menyiapkan jawaban…
                                    </small>
                                </div>
                            )}
                        </section>
                    )}

                    <div ref={bottom} />
                </div>

                <footer className="composer-area">
                    <div className="composer-wrap">
                        {error && (
                            <div
                                className="error-banner"
                                role="alert"
                            >
                                <span>{error}</span>

                                <button
                                    className="icon-button"
                                    aria-label="Tutup pesan kesalahan"
                                    onClick={() =>
                                        setError("")
                                    }
                                >
                                    <X size={16} />
                                </button>
                            </div>
                        )}

                        {quota?.blocked && (
                            <div
                                className="cooldown-banner"
                                role="status"
                            >
                                <Clock3 size={17} />

                                <span>
                                    100 pesanmu sudah terpakai.{" "}
                                    {seconds
                                        ? `Bisa chat lagi dalam ${countdown(seconds)}.`
                                        : "Mengisi ulang kuota…"}
                                </span>
                            </div>
                        )}

                        <form
                            className={`composer ${
                                quota?.blocked
                                    ? "composer-locked"
                                    : ""
                            }`}
                            onSubmit={event => {
                                event.preventDefault();
                                void send();
                            }}
                        >
                            <textarea
                                ref={input}
                                aria-label="Tulis pesan"
                                placeholder={
                                    quota?.blocked
                                        ? "Kuota sedang diisi ulang…"
                                        : "Ceritakan tujuan kariermu atau cari lowongan…"
                                }
                                value={text}
                                onChange={event =>
                                    setText(event.target.value)
                                }
                                maxLength={6000}
                                rows={1}
                                disabled={disabled}
                                onKeyDown={event => {
                                    if (
                                        event.key === "Enter" &&
                                        !event.shiftKey &&
                                        !event.nativeEvent
                                            .isComposing
                                    ) {
                                        event.preventDefault();
                                        void send();
                                    }
                                }}
                            />

                            <div className="composer-bottom">
                                <span>
                                    <Sparkles size={13} />
                                    TemuKerja Assistant
                                </span>

                                <div>
                                    <small>
                                        {text.length > 0
                                            ? `${text.length}/6000`
                                            : "Enter untuk kirim"}
                                    </small>

                                    <button
                                        className="send-button"
                                        type="submit"
                                        aria-label="Kirim pesan"
                                        disabled={
                                            disabled ||
                                            !text.trim()
                                        }
                                    >
                                        {busy === "send" ? (
                                            <LoaderCircle
                                                size={19}
                                                className="spin"
                                            />
                                        ) : (
                                            <ArrowUp size={20} />
                                        )}
                                    </button>
                                </div>
                            </div>
                        </form>

                        <p className="composer-disclaimer">
                            TemuKerja dapat keliru. Periksa
                            kembali informasi di sumber
                            lowongan.
                        </p>
                    </div>
                </footer>
            </main>

            <dialog
                ref={dialog}
                className="conversation-dialog"
                onClose={() => setDialogMode(null)}
                onCancel={event => {
                    if (busy) event.preventDefault();
                }}
            >
                <form onSubmit={submitDialog}>
                    <span className="dialog-symbol">
                        {dialogMode === "rename" ? (
                            <Pencil size={21} />
                        ) : (
                            <Trash2 size={21} />
                        )}
                    </span>

                    <h2>
                        {dialogMode === "rename"
                            ? "Ubah judul percakapan"
                            : "Hapus percakapan ini?"}
                    </h2>

                    {dialogMode === "rename" ? (
                        <label>
                            Judul
                            <input
                                value={title}
                                onChange={event =>
                                    setTitle(event.target.value)
                                }
                                minLength={1}
                                maxLength={120}
                                required
                                autoFocus
                                disabled={Boolean(busy)}
                            />
                        </label>
                    ) : (
                        <p>
                            “{selected?.title}” beserta isinya
                            akan dihapus. Kuota yang sudah
                            terpakai tetap dihitung.
                        </p>
                    )}

                    {dialogError && (
                        <p
                            className="error-box"
                            role="alert"
                        >
                            {dialogError}
                        </p>
                    )}

                    <div className="dialog-actions">
                        <button
                            type="button"
                            className="secondary"
                            onClick={() =>
                                dialog.current?.close()
                            }
                            disabled={Boolean(busy)}
                        >
                            Batal
                        </button>

                        <button
                            className={
                                dialogMode === "delete"
                                    ? "danger"
                                    : "primary"
                            }
                            disabled={
                                Boolean(busy) ||
                                (dialogMode === "rename" &&
                                    !title.trim())
                            }
                        >
                            {busy === "edit"
                                ? "Memproses…"
                                : dialogMode === "rename"
                                  ? "Simpan judul"
                                  : "Hapus percakapan"}
                        </button>
                    </div>
                </form>
            </dialog>
        </div>
    );
}