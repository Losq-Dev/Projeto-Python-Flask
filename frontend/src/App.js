import React, { useEffect, useMemo, useState } from "react";

/* =============================
   ⚙️ CONFIG
   ============================= */
const API_URL = "http://localhost:5000";

// recurso -> endpoint
const RESOURCES = {
  categorias: "/categorias",
  clientes: "/clientes",
  docas: "/docas",
  fornecedores: "/fornecedores",
  produtos: "/produtos",
  vendas: "/vendas",
};

/**
 * Campos exibidos por recurso (somente UI).
 * O mapeamento para o payload real é feito em buildPayload().
 */
const RESOURCE_FIELDS = {
  categorias: [{ name: "nome", label: "Nome", required: true }],

  clientes: [
    {
      name: "cpf",
      label: "CPF (apenas números)",
      type: "number",
      required: true,
    },
    { name: "nome", label: "Nome", required: true },
  ],

  // DOCAS: somente Produto ID (opcional), compatível com o backend atual
  docas: [
    { name: "produto_id", label: "Produto ID (opcional)", type: "number" },
  ],

  fornecedores: [
    {
      name: "cnpj",
      label: "CNPJ (apenas números)",
      type: "number",
      required: true,
    },
    { name: "nome", label: "Nome da Empresa", required: true },
    { name: "categoria_id", label: "Categoria ID (opcional)", type: "number" },
  ],

  produtos: [
    { name: "nome", label: "Nome", required: true }, // -> nome_produto
    { name: "validade", label: "Validade", type: "date", required: true }, // -> validade (YYYY-MM-DD)
    { name: "sku", label: "Lote (SKU)", type: "number", required: true }, // -> lote
    {
      name: "categoria_id",
      label: "Categoria ID",
      type: "number",
      required: true,
    }, // -> categoria
    {
      name: "fornecedor_cnpj",
      label: "Fornecedor CNPJ",
      type: "number",
      required: true,
    }, // -> fornecedor
    { name: "doca_id", label: "Doca ID (opcional)", type: "number" }, // -> doca
    {
      name: "preco",
      label: "Preço",
      type: "number",
      step: "0.01",
      required: true,
    }, // -> valor
  ],

  vendas: [
    {
      name: "valor",
      label: "Valor",
      type: "number",
      step: "0.01",
      required: true,
    },
    { name: "quantidade", label: "Quantidade", type: "number", required: true },
    { name: "produto_id", label: "Produto ID", type: "number", required: true },
    { name: "cliente_cpf", label: "Cliente CPF (opcional)", type: "number" },
    {
      name: "data_venda",
      label: "Data da Venda",
      type: "date",
      required: true,
    },
  ],
};

/* =============================
   🧰 Utils
   ============================= */
async function apiFetch(path, init) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(txt || `Erro ${res.status}`);
  }
  return res.json();
}

function cx(...xs) {
  return xs.filter(Boolean).join(" ");
}

/**
 * Constrói o payload que a API Flask espera, a partir do form da UI.
 */
function buildPayload(resource, form, isEdit) {
  switch (resource) {
    case "categorias":
      return {
        ...(isEdit
          ? {}
          : form.id_categoria
          ? { id_categoria: Number(form.id_categoria) }
          : {}),
        nome_categoria: form.nome,
      };

    case "clientes":
      return {
        ...(isEdit ? {} : { cpf: Number(form.cpf) }),
        nome_cliente: form.nome,
      };

    case "docas":
      return {
        // id_doca é opcional no create (autoincrement) – deixamos fora por padrão
        ...(isEdit
          ? {}
          : form.id_doca
          ? { id_doca: Number(form.id_doca) }
          : {}),
        produto: form.produto_id ? Number(form.produto_id) : null,
      };

    case "fornecedores":
      return {
        ...(isEdit ? {} : { cnpj: Number(form.cnpj) }),
        nome_empresa: form.nome,
        categoria: form.categoria_id ? Number(form.categoria_id) : null,
      };

    case "produtos":
      return {
        ...(isEdit
          ? {}
          : form.id_produto
          ? { id_produto: Number(form.id_produto) }
          : {}),
        nome_produto: form.nome,
        validade: form.validade, // YYYY-MM-DD
        lote: Number(form.sku),
        categoria: Number(form.categoria_id),
        fornecedor: Number(form.fornecedor_cnpj),
        doca: form.doca_id ? Number(form.doca_id) : null,
        valor: Number(form.preco),
      };

    case "vendas":
      return {
        ...(isEdit
          ? {}
          : form.id_venda
          ? { id_venda: Number(form.id_venda) }
          : {}),
        valor: Number(form.valor),
        quantidade: Number(form.quantidade),
        produto: Number(form.produto_id),
        cliente_cpf:
          form.cliente_cpf !== undefined && form.cliente_cpf !== ""
            ? Number(form.cliente_cpf)
            : null,
        data_venda: form.data_venda, // YYYY-MM-DD
      };

    default:
      return form;
  }
}

/* =============================
   🧱 Componentes
   ============================= */
function Toolbar({ tabs, active, onChange }) {
  return (
    <div className="w-full flex flex-wrap gap-2 items-center mb-4">
      {tabs.map((t) => (
        <button
          key={t}
          onClick={() => onChange(t)}
          className={cx(
            "px-3 py-2 rounded-2xl shadow-sm border",
            active === t
              ? "bg-gray-100 border-gray-300"
              : "bg-white hover:bg-gray-50"
          )}
        >
          {t}
        </button>
      ))}
    </div>
  );
}

function SearchBar({ value, onChange }) {
  return (
    <input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder="Buscar…"
      className="w-full md:w-80 border rounded-xl px-3 py-2 outline-none focus:ring"
    />
  );
}

function DataTable({ items, onEdit, onDelete }) {
  const keys = useMemo(() => (items[0] ? Object.keys(items[0]) : []), [items]);
  return (
    <div className="overflow-auto border rounded-2xl">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50">
          <tr>
            {keys.map((k) => (
              <th
                className="text-left px-3 py-2 font-medium text-gray-700"
                key={k}
              >
                {k}
              </th>
            ))}
            <th className="px-3 py-2" />
          </tr>
        </thead>
        <tbody>
          {items.map((row, idx) => (
            <tr
              className={idx % 2 ? "bg-white" : "bg-gray-50/50"}
              key={row.id || idx}
            >
              {keys.map((k) => (
                <td className="px-3 py-2 whitespace-nowrap" key={k}>
                  {String(row[k])}
                </td>
              ))}
              <td className="px-3 py-2 whitespace-nowrap flex gap-2">
                <button
                  className="text-blue-600 hover:underline"
                  onClick={() => onEdit(row)}
                >
                  Editar
                </button>
                <button
                  className="text-red-600 hover:underline"
                  onClick={() => onDelete(row)}
                >
                  Excluir
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function UpsertForm({ resource, fields, initial, onCancel, onSaved }) {
  const [form, setForm] = useState(() => initial || {});
  const [loading, setLoading] = useState(false);
  const isEdit = Boolean(initial && initial.id);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = buildPayload(resource, form, isEdit);
      const method = isEdit ? "PUT" : "POST";
      const path = isEdit
        ? `${RESOURCES[resource]}/${initial.id}`
        : RESOURCES[resource];

      const saved = await apiFetch(path, {
        method,
        body: JSON.stringify(payload),
      });
      onSaved(saved);
    } catch (err) {
      try {
        const pretty = JSON.stringify(JSON.parse(err.message), null, 2);
        alert(`Erro ao salvar:\n${pretty}`);
      } catch {
        alert(`Erro ao salvar: ${err.message}`);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {fields.map((f) => (
        <div key={f.name} className="grid gap-1">
          <label className="text-sm text-gray-600">{f.label}</label>
          <input
            type={f.type || "text"}
            step={f.step}
            className="border rounded-xl px-3 py-2"
            value={form[f.name] ?? ""}
            onChange={(e) => setForm({ ...form, [f.name]: e.target.value })}
            required={Boolean(f.required)}
          />
        </div>
      ))}
      <div className="flex gap-2 pt-2">
        <button
          type="submit"
          className="px-4 py-2 rounded-xl bg-black text-white disabled:opacity-50"
          disabled={loading}
        >
          {loading ? "Salvando…" : isEdit ? "Atualizar" : "Criar"}
        </button>
        <button
          type="button"
          className="px-4 py-2 rounded-xl border"
          onClick={onCancel}
        >
          Cancelar
        </button>
      </div>
    </form>
  );
}

function ResourceView({ resource }) {
  const [data, setData] = useState([]);
  const [q, setQ] = useState("");
  const [editing, setEditing] = useState(null);
  const [creating, setCreating] = useState(false);
  const fields = RESOURCE_FIELDS[resource] || [];

  async function load() {
    try {
      const res = await apiFetch(RESOURCES[resource]);
      const list = Array.isArray(res) ? res : res.items || res[resource] || [];
      setData(list);
    } catch (err) {
      alert(`Erro ao carregar: ${err.message}`);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resource]);

  async function remove(row) {
    if (!window.confirm(`Excluir ${resource} #${row.id || "(sem id)"}?`))
      return;
    try {
      await apiFetch(`${RESOURCES[resource]}/${row.id}`, { method: "DELETE" });
      await load();
    } catch (err) {
      alert(`Erro ao excluir: ${err.message}`);
    }
  }

  const filtered = () => {
    if (!q) return data;
    const term = q.toLowerCase();
    return data.filter((row) =>
      JSON.stringify(row).toLowerCase().includes(term)
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3 justify-between">
        <SearchBar value={q} onChange={setQ} />
        <div className="flex gap-2">
          <button className="px-3 py-2 rounded-xl border" onClick={load}>
            Recarregar
          </button>
          <button
            className="px-3 py-2 rounded-xl bg-black text-white"
            onClick={() => {
              setCreating(true);
              setEditing(null);
            }}
          >
            + Novo
          </button>
        </div>
      </div>

      {(creating || editing) && (
        <div className="p-4 border rounded-2xl bg-gray-50">
          <UpsertForm
            resource={resource}
            fields={fields}
            initial={editing || undefined}
            onCancel={() => {
              setCreating(false);
              setEditing(null);
            }}
            onSaved={() => {
              setCreating(false);
              setEditing(null);
              load();
            }}
          />
        </div>
      )}

      <DataTable
        items={filtered()}
        onEdit={(r) => {
          setEditing(r);
          setCreating(false);
        }}
        onDelete={remove}
      />
    </div>
  );
}

/* =============================
   🖥️ App principal
   ============================= */
export default function App() {
  const [tab, setTab] = useState("produtos"); // aba inicial

  return (
    <div className="p-6 max-w-7xl mx-auto text-gray-900">
      <header className="mb-6">
        <h1 className="text-2xl font-semibold">📦 Gestão de Estoque – UI</h1>
        <p className="text-gray-600">
          Interface simples para consumir sua API Flask (CRUD básico).
        </p>
      </header>

      <Toolbar
        tabs={Object.keys(RESOURCES)}
        active={tab}
        onChange={(t) => setTab(t)}
      />

      <div className="mt-4">
        <ResourceView resource={tab} />
      </div>

      <footer className="mt-10 text-xs text-gray-500">
        Base URL da API: <code>{API_URL}</code>
      </footer>
    </div>
  );
}
