"use client";

import { useEffect, useRef } from "react";
import { Terminal } from "xterm";
import { FitAddon } from "xterm-addon-fit";
import "xterm/css/xterm.css";
import type { MozaEvent } from "@/lib/api";

interface Props {
  events: MozaEvent[];
}

export default function TerminalComponent({ events }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const terminalRef = useRef<Terminal | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const renderedCount = useRef(0);

  useEffect(() => {
    if (!containerRef.current) return;

    const term = new Terminal({
      cursorBlink: true,
      cursorStyle: "block",
      fontSize: 13,
      fontFamily: "'JetBrains Mono', 'Cascadia Code', 'Fira Code', monospace",
      theme: {
        background: "#0d1117",
        foreground: "#e6edf3",
        cursor: "#58a6ff",
        black: "#484f58",
        red: "#ff7b72",
        green: "#3fb950",
        yellow: "#d29922",
        blue: "#58a6ff",
        magenta: "#bc8cff",
        cyan: "#39c5cf",
        white: "#b1bac4",
        brightBlack: "#6e7681",
        brightRed: "#ffa198",
        brightGreen: "#56d364",
        brightYellow: "#e3b341",
        brightBlue: "#79c0ff",
        brightMagenta: "#d2a8ff",
        brightCyan: "#56d4dd",
        brightWhite: "#f0f6fc",
      },
    });

    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.open(containerRef.current);
    fitAddon.fit();

    terminalRef.current = term;
    fitAddonRef.current = fitAddon;

    term.writeln("MOZA Terminal Session");

    return () => {
      term.dispose();
      terminalRef.current = null;
      fitAddonRef.current = null;
    };
  }, []);

  useEffect(() => {
    const term = terminalRef.current;
    if (!term) return;

    const newEvents = events.slice(renderedCount.current);
    for (const event of newEvents) {
      renderedCount.current += 1;

      if (event.type === "tool_call") {
        const args = event.payload.args as Record<string, unknown> | undefined;
        const command = args?.command as string | undefined;
        if (command) {
          term.writeln(`\r\n\x1b[32m$\x1b[0m ${command}`);
        }
      } else if (event.type === "tool_result") {
        const stdout = event.payload.stdout as string | undefined;
        const exitCode = event.payload.exit_code as number | null | undefined;
        if (stdout) {
          const lines = stdout.replace(/\n$/, "").split("\n");
          for (const line of lines) {
            term.writeln(line);
          }
        }
        if (exitCode !== undefined && exitCode !== null && exitCode !== 0) {
          term.writeln(`\x1b[31mexit code: ${exitCode}\x1b[0m`);
        }
      }
    }
  }, [events]);

  useEffect(() => {
    const fit = () => fitAddonRef.current?.fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, []);

  return (
    <div
      ref={containerRef}
      className="overflow-hidden rounded-xl border border-zinc-700/50"
      style={{ height: 240 }}
    />
  );
}
