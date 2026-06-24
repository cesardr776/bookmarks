# Setup do Frontend (Flutter)

## Pré-requisitos

- Flutter 3.22+ (`flutter --version`)
- Android Studio ou Xcode
- Projeto Firebase configurado

## Configuração Firebase

### 1. Instalar FlutterFire CLI

```bash
dart pub global activate flutterfire_cli
```

### 2. Configurar Firebase

```bash
cd frontend
flutterfire configure --project=seu-projeto-firebase
```

Isso vai criar `lib/firebase_options.dart` automaticamente.

### 3. Ativar Google Sign-In no Firebase

1. Firebase Console > Authentication > Sign-in method
2. Ative "Google"
3. Adicione o SHA-1 do seu app Android

### 4. Variáveis de ambiente

```bash
cp .env.example .env  # ou edite .env diretamente
```

```env
API_BASE_URL=https://seu-backend.com/api/v1
```

## Instalação

```bash
cd frontend
flutter pub get
```

## Execução

```bash
# Android
flutter run -d android

# iOS
flutter run -d ios

# Web (experimental)
flutter run -d chrome
```

## Build para produção

### Android (APK)

```bash
flutter build apk --release
# Saída: build/app/outputs/flutter-apk/app-release.apk
```

### Android (App Bundle para Play Store)

```bash
flutter build appbundle --release
```

### iOS

```bash
flutter build ipa --release
```

## Personalização

### Alterar URL da API

Edite `frontend/.env`:

```env
API_BASE_URL=https://api.seudominio.com/api/v1
```

### Temas

O tema é definido em `lib/config/app_theme.dart`. Para alterar a cor primária:

```dart
static const _seedColor = Color(0xFF6750A4); // mude aqui
```
