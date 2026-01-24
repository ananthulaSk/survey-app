# Flutter Web Development Rules

## Design Philosophy
- **No Material Default:** Avoid the default "Flutter Blue". Use a custom `ThemeData` defined in `main.dart`.
- **Responsive First:** Always assume the screen size can change. Use `LayoutBuilder` and `MediaQuery` to adapt UI for Mobile vs Desktop.

## Widget Patterns
- **Charts:** Use `fl_chart` for all data viz. Ensure charts have tooltips enabled for Desktop users (mouse hover).
- **State Management:** Keep business logic outside of UI widgets.
- **Consts:** Use `const` constructors everywhere possible to optimize Web rendering performance.

## Specific Implementations
- **Icons:** Use `cupertino_icons` as the primary icon set.
- **Networking:** All API calls must go through a dedicated service layer using the `http` package, not called directly inside widgets.
- **Storage:** Use `shared_preferences` for storing simple session data (like authentication tokens).
