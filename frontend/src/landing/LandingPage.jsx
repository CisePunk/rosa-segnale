import React, { useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  Check,
  ClipboardList,
  Columns3,
  History,
  Menu,
  MessageSquareText,
  PhoneCall,
  ShieldCheck,
  SlidersHorizontal,
  X,
} from "lucide-react";
import "./landing.css";

/* La demo reale è l'esperienza pubblica dell'applicazione, servita alla radice "/". */
const DEMO_URL = "/";

const NAV = [
  { label: "Home", id: "home" },
  { label: "Il problema", id: "problema" },
  { label: "Funzionalità", id: "funzionalita" },
  { label: "Come collaborare", id: "collaborazione" },
  { label: "Vantaggi", id: "vantaggi" },
  { label: "Contatti", id: "contatti" },
];

const prefersReducedMotion = () =>
  typeof window !== "undefined" &&
  window.matchMedia &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/* Scroll a un'ancora interna con offset per l'header sticky. */
function scrollToId(id) {
  const el = document.getElementById(id);
  if (!el) return;
  const y = el.getBoundingClientRect().top + window.scrollY - 74;
  window.scrollTo({ top: y, behavior: prefersReducedMotion() ? "auto" : "smooth" });
}

function BrandLockup() {
  return (
    <a
      className="ls-brand"
      href="#home"
      onClick={(e) => {
        e.preventDefault();
        scrollToId("home");
      }}
    >
      <span className="ls-brand__mark" aria-hidden="true">
        <span />
      </span>
      Rosa Segnale
    </a>
  );
}

/* -------------------- HEADER -------------------- */
function LandingHeader() {
  const [open, setOpen] = useState(false);
  // Sezione in cui ci si trova scorrendo: la marchiamo nel menu con un
  // cerchio+pallino (stile radio), non con una freccia. Il pallino marca la voce
  // scelta con calma; la freccia, invece, punterebbe e comanderebbe l'occhio.
  const [attiva, setAttiva] = useState("home");

  useEffect(() => {
    const sezioni = NAV.map((n) => document.getElementById(n.id)).filter(Boolean);
    if (!("IntersectionObserver" in window) || !sezioni.length) return;
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) setAttiva(e.target.id);
        });
      },
      // Banda sottile a ~metà schermo: è attiva la sezione che la attraversa.
      { rootMargin: "-45% 0px -50% 0px", threshold: 0 }
    );
    sezioni.forEach((s) => io.observe(s));
    return () => io.disconnect();
  }, []);

  const go = (id) => (e) => {
    e.preventDefault();
    setOpen(false);
    scrollToId(id);
  };

  return (
    <header className="ls-header">
      <div className="ls-wrap ls-header__inner">
        <BrandLockup />

        <nav className={open ? "ls-nav ls-nav--open" : "ls-nav"} aria-label="Navigazione principale">
          {NAV.map((item) => (
            <a
              key={item.id}
              href={`#${item.id}`}
              onClick={go(item.id)}
              className={attiva === item.id ? "is-active" : undefined}
              aria-current={attiva === item.id ? "true" : undefined}
            >
              <span className="ls-nav__dot" aria-hidden="true" />
              {item.label}
            </a>
          ))}
          <a className="ls-btn ls-btn-primary ls-btn-sm" href="#contatti" onClick={go("contatti")}>
            Richiedi una demo
          </a>
        </nav>

        <div className="ls-header__actions">
          <a className="ls-btn ls-btn-primary ls-btn-sm ls-cta-header" href="#contatti" onClick={go("contatti")}>
            Richiedi una demo
          </a>
          <button
            type="button"
            className="ls-menu-btn"
            aria-label={open ? "Chiudi il menu" : "Apri il menu"}
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
          >
            {open ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>
    </header>
  );
}

/* -------------------- MOCKUP: esperienza pubblica -------------------- */
function PublicMockup() {
  return (
    <div className="ls-browser" role="img" aria-label="Anteprima dell'esperienza pubblica di Rosa Segnale: risorse rapide e spazio di ascolto.">
      <div className="ls-browser__bar">
        <div className="ls-browser__dots"><i /><i /><i /></div>
        <div className="ls-browser__url">rosa-segnale · ascolto</div>
      </div>
      <div className="ls-browser__body">
        <div className="ls-mk-row">
          <div className="ls-mk-brand"><span aria-hidden="true" /> Rosa Segnale</div>
          <div className="ls-mk-toggle"><b>Ascolto</b><i>Area interna</i></div>
        </div>
        <div className="ls-mk-label">Risorse rapide</div>
        <div className="ls-mk-chips">
          <div className="ls-mk-chip"><b>112</b><span>Emergenza</span></div>
          <div className="ls-mk-chip"><b>1522</b><span>Antiviolenza</span></div>
        </div>
        <div className="ls-mk-panel">
          <div className="ls-mk-label" style={{ margin: 0 }}>Spazio di ascolto</div>
          <div className="ls-mk-textarea" />
          <div className="ls-mk-send">Invia</div>
        </div>
      </div>
    </div>
  );
}

/* -------------------- MOCKUP: revisione interna -------------------- */
function InternalMockup() {
  return (
    <div className="ls-dash" role="img" aria-label="Anteprima dell'ambiente interno di revisione: riepilogo, categorizzazione, indicatori, fonti e report.">
      <div className="ls-dash__head">
        <b>Revisione segnalazione</b>
        <span className="ls-dash__tag">In corso</span>
      </div>
      <div className="ls-dash__body">
        <div className="ls-dash__block">
          <b>Riepilogo</b>
          <div className="ls-dash__line" style={{ width: "92%" }} />
          <div className="ls-dash__line" style={{ width: "76%" }} />
        </div>
        <div className="ls-dash__grid2">
          <div className="ls-dash__block">
            <b>Categorizzazione</b>
            <div className="ls-dash__tags">
              <span className="ls-dash__tag">Messaggio breve</span>
              <span className="ls-dash__tag">Orientamento</span>
            </div>
          </div>
          <div className="ls-dash__block">
            <b>Indicatori</b>
            <div className="ls-dash__meters">
              <div className="ls-dash__meter"><i style={{ width: "70%" }} /></div>
              <div className="ls-dash__meter"><i style={{ width: "45%" }} /></div>
              <div className="ls-dash__meter"><i style={{ width: "60%" }} /></div>
            </div>
          </div>
        </div>
        <div className="ls-dash__block">
          <b>Fonti consultate · Output · Audit log</b>
          <div className="ls-dash__line" style={{ width: "88%" }} />
          <div className="ls-dash__line" style={{ width: "64%" }} />
        </div>
      </div>
    </div>
  );
}

/* -------------------- HERO -------------------- */
function Hero() {
  return (
    <section id="home" className="ls-hero" aria-labelledby="hero-title">
      <div className="ls-wrap ls-hero__grid">
        <div className="ls-hero__text ls-reveal">
          <p className="ls-eyebrow">Ascolto · Orientamento · Tracciabilità</p>
          <h1 id="hero-title" className="ls-h1">
            Trasformare una richiesta di aiuto in un percorso leggibile, tracciabile e responsabile.
          </h1>
          <p className="ls-lead">
            Rosa Segnale supporta enti e operatori nell'ascolto, nell'orientamento e nel triage non
            diagnostico delle segnalazioni delicate, mantenendo distinti accesso pubblico, revisione
            interna e controllo umano.
          </p>
          <div className="ls-hero__actions">
            <a
              className="ls-btn ls-btn-primary"
              href="#contatti"
              onClick={(e) => { e.preventDefault(); scrollToId("contatti"); }}
            >
              Richiedi una demo <ArrowRight size={18} aria-hidden="true" />
            </a>
            <a
              className="ls-btn ls-btn-secondary"
              href="#funzionalita"
              onClick={(e) => { e.preventDefault(); scrollToId("funzionalita"); }}
            >
              Scopri come funziona
            </a>
          </div>
          <p className="ls-micro ls-hero__micro">
            Nessun impegno: il confronto iniziale serve a verificare se il progetto è compatibile con
            il vostro contesto operativo.
          </p>
        </div>
        <div className="ls-hero__media ls-reveal">
          <PublicMockup />
        </div>
      </div>
    </section>
  );
}

/* -------------------- PROBLEMA -------------------- */
function Problema() {
  const punti = [
    "Le richieste possono essere brevi o incomplete.",
    "Una persona può non riuscire a spiegare tutto.",
    "Le informazioni si disperdono tra chat, note e passaggi manuali.",
    "Serve continuità tra ascolto, orientamento e revisione, con piena tracciabilità.",
  ];
  return (
    <section id="problema" className="ls-section ls-section--alt" aria-labelledby="problema-title">
      <div className="ls-wrap">
        <div className="ls-split ls-split--reverse">
          <div className="ls-split__media ls-reveal">
            <InternalMockup />
          </div>
          <div className="ls-reveal">
            <p className="ls-eyebrow">Il problema</p>
            <h2 id="problema-title" className="ls-h2">
              Quando il messaggio è breve, il contesto diventa essenziale.
            </h2>
            <p className="ls-lead">
              Le richieste di aiuto non arrivano sempre in modo completo o lineare. Possono essere
              frammentarie, ambigue o difficili da interpretare senza conoscere il contesto.
            </p>
            <ul className="ls-checklist">
              {punti.map((p) => (
                <li key={p}>
                  <span className="ls-ic" aria-hidden="true"><Check size={15} /></span>
                  {p}
                </li>
              ))}
            </ul>
            <p className="ls-micro" style={{ marginTop: 18 }}>
              La tecnologia deve supportare, non sostituire, la valutazione umana.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

/* -------------------- FUNZIONALITÀ -------------------- */
function Funzionalita() {
  return (
    <section id="funzionalita" className="ls-section" aria-labelledby="funzionalita-title">
      <div className="ls-wrap">
        <div className="ls-section__head">
          <p className="ls-eyebrow">Funzionalità</p>
          <h2 id="funzionalita-title" className="ls-h2">Due ambienti distinti, un unico percorso informativo.</h2>
        </div>

        {/* Blocco 1: esperienza pubblica */}
        <div className="ls-split ls-reveal">
          <div className="ls-split__media"><PublicMockup /></div>
          <div>
            <h3 className="ls-h3">Uno spazio discreto per iniziare a raccontare</h3>
            <p className="ls-muted">
              Un accesso semplice ed essenziale, che aiuta la persona a descrivere la situazione con i
              propri tempi. Il progetto gestisce con prudenza i messaggi brevi, indica i canali
              ufficiali e affianca la persona con un linguaggio non diagnostico, attento alla
              condizione di stress.
            </p>
            <div className="ls-feature-tags" aria-hidden="true">
              <span>Accesso semplice</span>
              <span>Messaggi brevi</span>
              <span>Canali ufficiali</span>
              <span>Supporto basato su fonti</span>
            </div>
          </div>
        </div>

        {/* Blocco 2: revisione interna */}
        <div className="ls-split ls-split--reverse ls-feature-block ls-reveal">
          <div className="ls-split__media"><InternalMockup /></div>
          <div>
            <h3 className="ls-h3">Informazioni organizzate per la revisione dell'operatore</h3>
            <p className="ls-muted">
              Riepilogo, categorizzazione, indicatori, trascrizione, fonti consultate e output vengono
              organizzati per rendere più leggibile il contesto. Cronologia, report e audit log
              mantengono tracciabili i passaggi, sempre sotto controllo umano.
            </p>
            <div className="ls-feature-tags" aria-hidden="true">
              <span>Riepilogo</span>
              <span>Categorizzazione</span>
              <span>Cronologia</span>
              <span>Report</span>
              <span>Audit log</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* -------------------- COLLABORAZIONE (3 passi commerciali) -------------------- */
function Collaborazione() {
  const steps = [
    {
      num: "01",
      title: "Partiamo dal vostro contesto operativo",
      text: "Raccogliamo obiettivi, destinatari, flussi esistenti, modalità di gestione delle segnalazioni e principali vincoli organizzativi.",
      note: "Il primo confronto serve a verificare se Rosa Segnale è realmente pertinente.",
      action: "Prenota il confronto",
    },
    {
      num: "02",
      title: "Verifichiamo Rosa Segnale sui vostri casi d'uso",
      text: "Presentiamo il progetto, mostriamo l'esperienza pubblica e l'ambiente interno e confrontiamo le funzionalità disponibili con le vostre esigenze.",
      note: "Individuiamo ciò che è già utilizzabile e gli eventuali adattamenti necessari.",
      action: "Richiedi la demo",
    },
    {
      num: "03",
      title: "Definiamo accordo, responsabilità e avvio",
      text: "Concordiamo obiettivi, perimetro, ruoli, tempi, gestione dei dati e modalità della sperimentazione o della collaborazione.",
      note: "Il risultato è un percorso definito, non una promessa commerciale generica.",
      action: "Avvia la valutazione",
      featured: true,
    },
  ];
  return (
    <section id="collaborazione" className="ls-section ls-section--alt" aria-labelledby="collab-title">
      <div className="ls-wrap">
        <div className="ls-section__head ls-section__head--center">
          <p className="ls-eyebrow">Come collaborare · 3 passi</p>
          <h2 id="collab-title" className="ls-h2">Dal primo confronto a una collaborazione definita.</h2>
        </div>
        <div className="ls-steps">
          {steps.map((s) => (
            <div key={s.num} className={s.featured ? "ls-step ls-step--featured ls-reveal" : "ls-step ls-reveal"}>
              <div className="ls-step__num">{s.num}</div>
              <h3 className="ls-h3">{s.title}</h3>
              <p className="ls-muted" style={{ margin: 0 }}>{s.text}</p>
              <p className="ls-step__note">{s.note}</p>
              <div className="ls-step__action">
                <a
                  className="ls-btn ls-btn-ghost"
                  href="#contatti"
                  onClick={(e) => { e.preventDefault(); scrollToId("contatti"); }}
                >
                  {s.action}
                </a>
              </div>
            </div>
          ))}
        </div>
        <div className="ls-steps__cta ls-reveal">
          <a
            className="ls-btn ls-btn-primary"
            href="#contatti"
            onClick={(e) => { e.preventDefault(); scrollToId("contatti"); }}
          >
            Parliamo del vostro progetto <ArrowRight size={18} aria-hidden="true" />
          </a>
          <p className="ls-micro">Il confronto iniziale non comporta l'attivazione automatica del servizio.</p>
        </div>
      </div>
    </section>
  );
}

/* -------------------- VANTAGGI -------------------- */
function Vantaggi() {
  const cards = [
    { icon: MessageSquareText, title: "Accesso discreto", text: "Un'interfaccia pubblica essenziale, progettata per ridurre il carico iniziale e facilitare l'avvio della richiesta." },
    { icon: ClipboardList, title: "Supporto alla revisione", text: "Le informazioni vengono organizzate per rendere più leggibile il contesto da parte dell'operatore." },
    { icon: History, title: "Tracciabilità", text: "Cronologia, fonti, passaggi e output rimangono consultabili durante il processo di revisione." },
    { icon: Columns3, title: "Separazione degli ambienti", text: "L'esperienza pubblica e l'ambiente interno restano distinti per funzione, destinatari e responsabilità." },
    { icon: ShieldCheck, title: "Risposte prudenti", text: "Il progetto mantiene un linguaggio orientativo, evitando diagnosi, automatismi e indicazioni non supportate." },
    { icon: SlidersHorizontal, title: "Adattabilità", text: "Rosa Segnale può essere valutato rispetto ai flussi, alle procedure e alle necessità operative dell'ente." },
  ];
  return (
    <section id="vantaggi" className="ls-section" aria-labelledby="vantaggi-title">
      <div className="ls-wrap">
        <div className="ls-section__head ls-section__head--center">
          <p className="ls-eyebrow">Vantaggi</p>
          <h2 id="vantaggi-title" className="ls-h2">Più continuità tra richiesta, orientamento e revisione.</h2>
        </div>
        <div className="ls-grid">
          {cards.map((c) => {
            const Icon = c.icon;
            return (
              <article key={c.title} className="ls-card ls-reveal">
                <div className="ls-card__ico" aria-hidden="true"><Icon size={22} /></div>
                <h3 className="ls-h3">{c.title}</h3>
                <p>{c.text}</p>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}

/* -------------------- CTA FINALE -------------------- */
function CtaFinale() {
  return (
    <section id="contatti" className="ls-section ls-section--alt" aria-labelledby="contatti-title">
      <div className="ls-wrap">
        <div className="ls-cta-final ls-reveal">
          <p className="ls-eyebrow">Richiedi una demo</p>
          <h2 id="contatti-title" className="ls-h2">
            Valutiamo se Rosa Segnale può entrare nel vostro flusso operativo.
          </h2>
          <p>
            Una demo guidata permette di verificare esperienza pubblica, revisione interna,
            tracciabilità e possibili adattamenti rispetto alle esigenze della vostra organizzazione.
          </p>
          <div className="ls-cta-final__actions">
            <a className="ls-btn ls-btn-primary" href={DEMO_URL}>
              Richiedi una demo <ArrowRight size={18} aria-hidden="true" />
            </a>
            <a
              className="ls-btn ls-btn-secondary"
              href="#funzionalita"
              onClick={(e) => { e.preventDefault(); scrollToId("funzionalita"); }}
            >
              Scopri come funziona
            </a>
          </div>
          <p className="ls-cta-note">
            Il pulsante apre l'esperienza pubblica reale. Un canale di contatto diretto (email o form)
            per prenotare un confronto è ancora da configurare.
          </p>
        </div>
      </div>
    </section>
  );
}

/* -------------------- FOOTER -------------------- */
function LandingFooter() {
  const year = new Date().getFullYear();
  const go = (id) => (e) => { e.preventDefault(); scrollToId(id); };
  return (
    <footer className="ls-footer">
      <div className="ls-wrap">
        <div className="ls-footer__grid">
          <div className="ls-footer__col">
            <BrandLockup />
            <p className="ls-footer__desc">
              Progetto di ascolto, orientamento e triage non diagnostico per situazioni delicate,
              con accesso pubblico e revisione interna distinti.
            </p>
          </div>
          <div className="ls-footer__col">
            <h4>Sezioni</h4>
            <ul>
              <li><a href="#problema" onClick={go("problema")}>Il problema</a></li>
              <li><a href="#funzionalita" onClick={go("funzionalita")}>Funzionalità</a></li>
              <li><a href="#collaborazione" onClick={go("collaborazione")}>Come collaborare</a></li>
              <li><a href="#vantaggi" onClick={go("vantaggi")}>Vantaggi</a></li>
            </ul>
          </div>
          <div className="ls-footer__col">
            <h4>In caso di pericolo immediato</h4>
            <div className="ls-emergency">
              <span><PhoneCall size={16} aria-hidden="true" /> <b>112</b> Emergenza</span>
              <span><PhoneCall size={16} aria-hidden="true" /> <b>1522</b> Antiviolenza e stalking</span>
            </div>
            <ul style={{ marginTop: 16 }}>
              <li><a href={DEMO_URL}>Prova l'esperienza pubblica</a></li>
            </ul>
          </div>
        </div>
        <p className="ls-footer__note">
          Rosa Segnale è un progetto di ascolto, orientamento e triage non diagnostico. Non sostituisce
          il 112, il 1522, le forze dell'ordine, i centri antiviolenza o i professionisti qualificati.
        </p>
        <p className="ls-footer__legal">© {year} Rosa Segnale</p>
      </div>
    </footer>
  );
}

/* -------------------- PAGINA -------------------- */
export default function LandingPage() {
  const rootRef = useRef(null);

  // Reveal leggero allo scroll (rispetta prefers-reduced-motion)
  useEffect(() => {
    const nodes = rootRef.current ? rootRef.current.querySelectorAll(".ls-reveal") : [];
    if (prefersReducedMotion() || !("IntersectionObserver" in window)) {
      nodes.forEach((n) => n.classList.add("is-visible"));
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
    );
    nodes.forEach((n) => io.observe(n));
    return () => io.disconnect();
  }, []);

  return (
    <div className="landing" ref={rootRef}>
      <a className="ls-skip" href="#home">Vai al contenuto</a>
      <LandingHeader />
      <main>
        <Hero />
        <Problema />
        <Funzionalita />
        <Collaborazione />
        <Vantaggi />
        <CtaFinale />
      </main>
      <LandingFooter />
    </div>
  );
}
