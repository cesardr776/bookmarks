import 'package:flutter_dotenv/flutter_dotenv.dart';

class AppConstants {
  static String get apiBaseUrl =>
      dotenv.env['API_BASE_URL'] ?? 'http://localhost:8000/api/v1';

  static const String generateEndpoint = '/generate';
  static const String appName = 'Moda IA';
  static const String appTagline = 'Fotos profissionais com IA';
}
