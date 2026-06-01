#!/usr/bin/env bash
# Despliegue automático en GitHub + Pages del Observatorio Aeronáutico.
# Uso:   bash deploy_github.sh [nombre-del-repo] [public|private]
# Ej:    bash deploy_github.sh aeronaves-oficiales public
#
# Requiere git. Si además tenés instalada la CLI de GitHub (gh) y estás logueado
# (gh auth login), crea el repo, activa Pages y los permisos AUTOMÁTICAMENTE.
# Si no tenés gh, te pide la URL del repo (creado a mano) y hace el push.
set -e
cd "$(dirname "$0")"

REPO="${1:-aeronaves-oficiales}"
VIS="${2:-public}"

echo "==> Preparando repositorio: $REPO ($VIS)"

# 1) Git init + commit
if [ ! -d .git ]; then git init -q; fi
git add .
git config user.name  >/dev/null 2>&1 || git config user.name  "Observatorio"
git config user.email >/dev/null 2>&1 || git config user.email "observatorio@example.com"
git commit -q -m "Observatorio aeronáutico - despliegue" || echo "   (sin cambios para commitear)"
git branch -M main

if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  echo "==> GitHub CLI detectada y autenticada. Automatizando todo."
  # 2) Crear repo y push (si ya existe, solo agrega remote y pushea)
  if ! gh repo view "$REPO" >/dev/null 2>&1; then
    gh repo create "$REPO" --"$VIS" --source=. --remote=origin --push
  else
    git remote get-url origin >/dev/null 2>&1 || git remote add origin "$(gh repo view "$REPO" --json sshUrl -q .sshUrl)"
    git push -u origin main
  fi
  OWNER="$(gh api user -q .login)"
  # 3) Permisos de Actions: lectura/escritura (para commitear datos)
  gh api -X PUT "repos/$OWNER/$REPO/actions/permissions/workflow" \
     -f default_workflow_permissions=write -F can_approve_pull_request_reviews=false >/dev/null 2>&1 || true
  # 4) Activar Pages con build por GitHub Actions
  gh api -X POST "repos/$OWNER/$REPO/pages" -f build_type=workflow >/dev/null 2>&1 \
    || gh api -X PUT "repos/$OWNER/$REPO/pages" -f build_type=workflow >/dev/null 2>&1 || true
  # 5) Disparar el workflow
  gh workflow run "deploy.yml" >/dev/null 2>&1 || true
  echo ""
  echo "==> LISTO."
  echo "    Repo:  https://github.com/$OWNER/$REPO"
  echo "    Sitio: https://$OWNER.github.io/$REPO/   (tarda 1-2 min en publicarse)"
  echo "    Seguí el avance en la pestaña Actions del repo."
else
  echo "==> No encontré la GitHub CLI autenticada."
  echo "    Opción A (recomendada): instalá 'gh' (https://cli.github.com), corré 'gh auth login' y volvé a ejecutar este script."
  echo "    Opción B (manual): creá un repo vacío en github.com y pegá su URL acá abajo."
  read -r -p "    URL del repo (o ENTER para cancelar): " URL
  if [ -n "$URL" ]; then
    git remote add origin "$URL" 2>/dev/null || git remote set-url origin "$URL"
    git push -u origin main
    echo ""
    echo "==> Push hecho. Ahora en el repo activá:"
    echo "    Settings > Pages > Source: GitHub Actions"
    echo "    Settings > Actions > General > Workflow permissions: Read and write"
  else
    echo "    Cancelado. No se subió nada."
  fi
fi
